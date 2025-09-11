from django.core.management.base import BaseCommand, CommandError
from site_management.models import SiteAPIKey, Site

class Command(BaseCommand):
    help = 'Gera uma nova chave de API para um Site e imprime a chave completa (mostrada apenas uma vez).'

    def add_arguments(self, parser):
        parser.add_argument('domain', help='Domínio completo ou parte única para localizar o site')
        parser.add_argument('--name', default='', help='Nome/descrição interna da chave')

    def handle(self, *args, **options):
        domain = options['domain']
        name = options['name']
        try:
            site = Site.objects.get(domain__icontains=domain)
        except Site.DoesNotExist:
            raise CommandError('Site não encontrado para o domínio informado')
        except Site.MultipleObjectsReturned:
            raise CommandError('Domínio não é específico o bastante (múltiplos sites encontrados)')

        instance, full_key = SiteAPIKey.create_key(site=site, name=name)
        self.stdout.write(self.style.SUCCESS('Chave criada com sucesso:'))
        self.stdout.write(full_key)
        self.stdout.write('Guarde este valor; ele não será mostrado novamente.')
