from datetime import date

from django.db import transaction

from apps.accounts.models import Account, Transfer
from apps.core.services.money import ZERO, money
from apps.transactions.models import Transaction


def _delta(account: Account, amount, tx_type: str, direction: str | None = None):
    amount = money(amount)
    if account.is_liability:
        if tx_type == Transaction.Type.EXPENSE:
            return amount
        if tx_type == Transaction.Type.INCOME:
            return -amount
        if tx_type == Transaction.Type.TRANSFER:
            return -amount if direction == "in" else amount
        return ZERO
    if tx_type == Transaction.Type.INCOME:
        return amount
    if tx_type == Transaction.Type.EXPENSE:
        return -amount
    if tx_type == Transaction.Type.TRANSFER:
        return amount if direction == "in" else -amount
    return ZERO


def apply_balance(account: Account, amount, tx_type: str, direction: str | None = None, reverse: bool = False):
    change = _delta(account, amount, tx_type, direction)
    if reverse:
        change = -change
    account.current_balance = money(account.current_balance) + change
    account.save(update_fields=["current_balance", "updated_at"])
    return account


def transfer_direction(tx: Transaction) -> str | None:
    if tx.transaction_type != Transaction.Type.TRANSFER or not tx.transfer_id:
        return None
    transfer = tx.transfer
    if transfer.from_transaction_id == tx.id:
        return "out"
    if transfer.to_transaction_id == tx.id:
        return "in"
    if transfer.from_account_id == tx.account_id:
        return "out"
    return "in"


@transaction.atomic
def create_transaction(*, user, account, amount, transaction_type, transaction_date, **fields) -> Transaction:
    amount = money(amount)
    if amount <= ZERO:
        raise ValueError("Please enter a valid amount.")
    tx = Transaction.objects.create(
        user=user,
        account=account,
        amount=amount,
        transaction_type=transaction_type,
        transaction_date=transaction_date,
        currency=fields.pop("currency", account.currency),
        **fields,
    )
    apply_balance(account, amount, transaction_type, transfer_direction(tx))
    return tx


@transaction.atomic
def update_transaction(tx: Transaction, **fields) -> Transaction:
    old_account = tx.account
    old_amount = money(tx.amount)
    old_type = tx.transaction_type
    old_direction = transfer_direction(tx)

    tag_ids = fields.pop("tag_ids", None)
    apply_balance(old_account, old_amount, old_type, old_direction, reverse=True)

    for key, value in fields.items():
        setattr(tx, key, value)
    if "amount" in fields:
        tx.amount = money(fields["amount"])
    tx.save()
    tx.refresh_from_db()

    apply_balance(tx.account, tx.amount, tx.transaction_type, transfer_direction(tx))
    if tag_ids is not None:
        tx.tags.set(tag_ids)
    return tx


@transaction.atomic
def delete_transaction(tx: Transaction):
    apply_balance(tx.account, tx.amount, tx.transaction_type, transfer_direction(tx), reverse=True)
    tx.delete()


@transaction.atomic
def create_transfer(*, user, from_account, to_account, amount, transfer_date, notes="", fee=ZERO) -> Transfer:
    amount = money(amount)
    fee = money(fee)
    if from_account.id == to_account.id:
        raise ValueError("Choose two different accounts.")
    if amount <= ZERO:
        raise ValueError("Please enter a valid amount.")

    transfer = Transfer.objects.create(
        user=user,
        from_account=from_account,
        to_account=to_account,
        amount=amount,
        fee=fee,
        transfer_date=transfer_date,
        notes=notes,
    )
    out_tx = Transaction.objects.create(
        user=user,
        account=from_account,
        amount=amount,
        transaction_type=Transaction.Type.TRANSFER,
        transaction_date=transfer_date,
        merchant="",
        description=f"Transfer to {to_account.name}",
        notes=notes,
        currency=from_account.currency,
        payment_method=Transaction.Method.BANK,
        transfer=transfer,
    )
    in_tx = Transaction.objects.create(
        user=user,
        account=to_account,
        amount=amount,
        transaction_type=Transaction.Type.TRANSFER,
        transaction_date=transfer_date,
        merchant="",
        description=f"Transfer from {from_account.name}",
        notes=notes,
        currency=to_account.currency,
        payment_method=Transaction.Method.BANK,
        transfer=transfer,
    )
    transfer.from_transaction = out_tx
    transfer.to_transaction = in_tx
    transfer.save(update_fields=["from_transaction", "to_transaction"])
    apply_balance(from_account, amount, Transaction.Type.TRANSFER, "out")
    apply_balance(to_account, amount, Transaction.Type.TRANSFER, "in")
    if fee > ZERO:
        create_transaction(
            user=user,
            account=from_account,
            amount=fee,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date=transfer_date,
            merchant="Transfer fee",
            description="Transfer fee",
            payment_method=Transaction.Method.BANK,
        )
    return transfer


@transaction.atomic
def delete_transfer(transfer: Transfer):
    if transfer.from_transaction_id:
        delete_transaction(transfer.from_transaction)
    if transfer.to_transaction_id:
        try:
            delete_transaction(transfer.to_transaction)
        except Transaction.DoesNotExist:
            pass
    transfer.delete()


def month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    from datetime import timedelta

    return start, end - timedelta(days=1)
