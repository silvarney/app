from django.test import TestCase
from django.utils import timezone
from accounts.models import Account
from django.contrib.auth import get_user_model
from .models import Site, TemplateCategory, PlanType, Item, SiteCategory, Service


class ServiceModelTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.owner = User.objects.create_user(email='owner@test.com', password='test123', username='owner')
		self.account = Account.objects.create(name='Conta Teste', owner=self.owner)
		self.template_cat = TemplateCategory.objects.create(
			name='Padrao', description='',
			desktop_image='templates/desktop/x.png',
			mobile_image='templates/mobile/x.png'
		)
		item = Item.objects.create(title='Item', description='Desc', value=10)
		self.plan = PlanType.objects.create(title='Plano', description='Desc', discount=0, template_category=self.template_cat)
		self.plan.items.add(item)
		self.site = Site.objects.create(
			account=self.account,
			domain='https://example.com',
			template_category=self.template_cat,
			plan_type=self.plan,
			status='active',
			expiration_date=timezone.now()
		)
		self.category = SiteCategory.objects.create(site=self.site, name='Cat')

	def test_link_and_order_auto_generated(self):
		service = Service.objects.create(site=self.site, category=self.category, title='Polimento Premium')
		self.assertTrue(service.link.startswith('/polimento-premium'))
		self.assertGreater(service.order, 0)

	def test_unique_link_increment_and_order_sequence(self):
		s1 = Service.objects.create(site=self.site, category=self.category, title='Lavagem')
		s2 = Service.objects.create(site=self.site, category=self.category, title='Lavagem')
		self.assertNotEqual(s1.link, s2.link)
		self.assertTrue(s2.link.startswith('/lavagem'))
		self.assertEqual(s1.order + 1, s2.order)
