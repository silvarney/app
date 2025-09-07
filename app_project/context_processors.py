from settings.models import GlobalSetting

def appearance_settings(request):
    """
    Context processor para carregar configurações de aparência globalmente
    """
    try:
        # Buscar configurações de aparência
        primary_color = GlobalSetting.objects.filter(key='primary_color').first()
        secondary_color = GlobalSetting.objects.filter(key='secondary_color').first()
        
        return {
            'global_primary_color': primary_color.value if primary_color else '#3B82F6',
            'global_secondary_color': secondary_color.value if secondary_color else '#6B7280',
        }
    except Exception:
        # Valores padrão em caso de erro
        return {
            'global_primary_color': '#3B82F6',
            'global_secondary_color': '#6B7280',
        }