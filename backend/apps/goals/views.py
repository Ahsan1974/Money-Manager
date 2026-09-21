from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Account
from apps.core.services.ledger import create_transfer
from apps.core.services.money import money
from apps.goals.models import GoalContribution, SavingsGoal
from apps.goals.serializers import GoalContributionSerializer, SavingsGoalSerializer


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    queryset = SavingsGoal.objects.all()

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user).prefetch_related("contributions")

    @action(detail=True, methods=["post"])
    def contribute(self, request, pk=None):
        goal = self.get_object()
        serializer = GoalContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = money(serializer.validated_data["amount"])
        contribution = GoalContribution.objects.create(goal=goal, **serializer.validated_data)
        goal.current_amount = money(goal.current_amount) + amount
        if goal.current_amount >= money(goal.target_amount):
            goal.status = SavingsGoal.Status.COMPLETED
        goal.save(update_fields=["current_amount", "status", "updated_at"])
        account_id = serializer.validated_data.get("account")
        if account_id and goal.linked_account_id and account_id.id != goal.linked_account_id:
            create_transfer(
                user=request.user,
                from_account=account_id,
                to_account=goal.linked_account,
                amount=amount,
                transfer_date=serializer.validated_data["contributed_on"],
                notes=f"Contribution to {goal.name}",
            )
        return Response(SavingsGoalSerializer(goal, context={"request": request}).data)
