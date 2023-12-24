import os

from splitwise import Splitwise
from FireflyIII import FireflyIII
from datetime import datetime
import pytz


class SW:

    def __init__(self, consumerKey, consumerSecret, apiKey):
        if not consumerKey or not consumerSecret or not apiKey:
            raise ValueError("Invalid Splitwise key or secrets")
        self.sw = Splitwise(consumerKey, consumerSecret, api_key=apiKey)
        self.limit = 20
        self.groups = None
        self.friends = None
        self.user = None
        self.getUser()

    def getGroups(self):
        self.groups = self.sw.getGroups()

    def getFriends(self):
        self.friends = self.sw.getFriends()

    def getUser(self):
        self.user = self.sw.getCurrentUser()

    def showGroups(self):
        # Use groups cache if available
        if not self.groups:
            self.getGroups()
        for group in self.groups:
            date = datetime.strptime(group.updated_at, "%Y-%m-%dT%H:%M:%SZ")
            gr_id = group.id
            print(f"Group [{group.name}][{gr_id}] - Updated: {date.day}/{date.month}/{date.year}")

    def getGroupName(self, groupId) -> str:
        """Extract the group name from the ID"""
        # Use groups cache if available
        if not self.groups:
            self.getGroups()
        # Extract the group
        for group in self.groups:
            if group.id == groupId:
                return group.name
        return "No group"

    def getFriendName(self, friendId) -> str:
        """Extract the friend name from the ID"""
        if not self.friends:
            self.getFriends()
        # Extract the friend
        for friend in self.friends:
            if friend.id == friendId:
                return f"{str(friend.first_name or '')} {str(friend.last_name or '')}".strip()
        return f"Friend #{friendId}"

    def exportToFirefly(self, ff: FireflyIII, default_src, default_dest,
                        tag, exportStartDate="2023-10-01", firstExport=False):
        """Massive export of transaction from Splitwise to Firefly III"""
        if tag is None or tag is not list:
            tag = ["Splitwise"]
        iteration_num = 0
        while True:
            offset = iteration_num * self.limit
            if firstExport:
                sw_expenses = self.sw.getExpenses(offset=offset, limit=self.limit, dated_after=exportStartDate)
            else:
                sw_expenses = self.sw.getExpenses(offset=offset, limit=self.limit, updated_after=exportStartDate)
            for expense in sw_expenses:
                self.processExpense(ff, expense, default_src, default_dest, tag)
            if len(sw_expenses) <= 0:
                print(f"Iterated {iteration_num + 1} times - Stop loop")
                break
            iteration_num += 1

    def processExpense(self, ff, expense, src, dest, defaultTags):
        date = datetime.strptime(expense.date, "%Y-%m-%dT%H:%M:%SZ")
        isDeleted = bool(expense.deleted_at)
        tag = defaultTags + [self.getGroupName(expense.group_id)]
        message = f"{'[DELETED]' if isDeleted else ''}[{expense.category.name}] {expense.description} - {expense.cost}{expense.currency_code} {date.day}/{date.month}/{date.year} [ID: {expense.id} - Group: {self.getGroupName(expense.group_id)}]"
        for user in expense.users:
            # Check if the expense refers to me
            nome_ok = (user.id == self.user.id)
            amount_ok = float(user.owed_share) > 0.0
            if nome_ok and amount_ok:
                # Search if the transaction already exists
                ff_transactions = ff.searchTransaction(f"external_id_is:{expense.id}")
                if ff_transactions and not isDeleted:
                    ff_update_date = datetime.strptime(ff_transactions[0]['attributes']['updated_at'],
                                                       '%Y-%m-%dT%H:%M:%S%z')
                    sw_update_date = datetime.strptime(expense.updated_at, "%Y-%m-%dT%H:%M:%SZ").astimezone(
                        pytz.timezone(os.getenv("TZ", "Etc/UTC")))
                    print(f"FF: {ff_update_date}- SW: {sw_update_date}")
                    if sw_update_date > ff_update_date:
                        # TODO Firefly III BUG
                        ff.updateTransaction(ff_id=ff_transactions[0]['id'],
                                             date=expense.date, amount=float(user.owed_share),
                                             description=expense.description,
                                             category=expense.category.name, message=message,
                                             tag=tag, splitExpense=self.isSplitExpense(expense))
                    else:
                        # No update required
                        print("No update required")
                elif ff_transactions and isDeleted:
                    ff.deleteTransaction(ff_transactions[0])
                elif not ff_transactions and not isDeleted:
                    # Inserting new transaction
                    ff.insertTransaction(date=expense.date, amount=float(user.owed_share),
                                         description=expense.description,
                                         category=expense.category.name,
                                         source=src, dest=dest, message=message, sw_id=expense.id,
                                         tag=tag, splitExpense=self.isSplitExpense(expense))
                else:
                    # Ignoring transaction deleted before first sync
                    pass
                # print(message)
                # print(f"Quota di {user.first_name}: {user.owed_share}{expense.currency_code}")
            elif not amount_ok:
                print(f"Ignoring this transaction: {message}")

    @staticmethod
    def isSplitExpense(sw_expense) -> bool:
        return (
                sw_expense.creation_method == "split"
                or
                (sw_expense.creation_method is None and not sw_expense.expense_payment)
        )

    def manageLiabilitiesToFirefly(self, ff):
        groups = self.sw.getGroups()
        for group in groups:
            debts = group.getSimplifiedDebts()
            for debt in debts:
                if debt.fromUser == self.user.id:
                    print(f"I owe {debt.amount}{debt.currency_code} to {self.getFriendName(debt.toUser)}")
                    print("Liabilietes export currently not implemented")
                elif debt.toUser == self.user.id:
                    print(f"I am owed {debt.amount}{debt.currency_code} by {self.getFriendName(debt.fromUser)}")
                    print("Liabilietes export currently not implemented")
                else:
                    print(f"I am not interested by this debt: {self.getFriendName(debt.fromUser)} owes {debt.amount}{debt.currency_code} by {self.getFriendName(debt.toUser)}")
