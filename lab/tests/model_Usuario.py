from django.test import TestCase
from ..models import Usuario, Escopo, SB


class UsuariosMethodTests(TestCase):

    def test_group_to_staff(self):
        '''The team member's user must be added to the 'default_users' group'''
        user = Usuario(username="member_staff", is_staff=True)
        user.save()
        list_group = [group.name for group in user.groups.all()]
        self.assertEqual('users_default' in list_group, True)

    def test_group_to_no_staff(self):
        '''The user who is not a team member must not be in any groups'''
        user = Usuario(username="member_no_staff", is_staff=False)
        user.save()
        self.assertEqual(len(user.groups.all()), 0)

    def test_group_to_user_removed_staff(self):
        '''The user who has been removed from the team must not belong to any groups'''
        user = Usuario(username="member_staff", is_staff=True)
        user.save()
        user.is_staff = False
        user.save()
        self.assertEqual(len(user.groups.all()), 0)

    def test_return_escopos(self):
        '''method 'get_escopos' should return all active escopos'''

        active_escopo_1 = Escopo(nome='Escopo 1').save()
        active_escopo_2 = Escopo(nome='Escopo 2').save()
        active_escopo_3 = Escopo(nome='Escopo 3').save()
        active_escopo_4 = Escopo(
            nome='Escopo 4', status=SB.INATIVO).save()
        active_escopo_5 = Escopo(
            nome='Escopo 5', status=SB.INATIVO).save()
        user = Usuario(username="test")
        self.assertEqual(len(user.get_escopos()), 3)
