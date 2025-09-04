from rest_framework import serializers
from .models import GlobalSetting, AccountSetting, UserSetting, SettingTemplate
from accounts.models import Account
from django.contrib.auth import get_user_model

User = get_user_model()


class GlobalSettingSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = GlobalSetting
        fields = [
            'id', 'key', 'value', 'typed_value', 'setting_type', 'description',
            'category', 'is_public', 'is_editable', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        """Retorna o valor convertido para o tipo correto"""
        try:
            return obj.get_typed_value()
        except (ValueError, TypeError, json.JSONDecodeError):
            return obj.value
    
    def validate_key(self, value):
        """Valida se a chave não contém caracteres especiais"""
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise serializers.ValidationError(
                "A chave deve conter apenas letras, números, pontos, hífens e underscores."
            )
        return value


class AccountSettingSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = AccountSetting
        fields = [
            'id', 'account', 'account_name', 'key', 'value', 'typed_value',
            'setting_type', 'description', 'category', 'is_inherited',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'account', 'created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        """Retorna o valor convertido para o tipo correto"""
        try:
            return obj.get_typed_value()
        except (ValueError, TypeError, json.JSONDecodeError):
            return obj.value
    
    def validate_key(self, value):
        """Valida se a chave não contém caracteres especiais"""
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise serializers.ValidationError(
                "A chave deve conter apenas letras, números, pontos, hífens e underscores."
            )
        return value


class UserSettingSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserSetting
        fields = [
            'id', 'user', 'user_email', 'key', 'value', 'typed_value',
            'setting_type', 'description', 'category', 'is_inherited',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        """Retorna o valor convertido para o tipo correto"""
        try:
            return obj.get_typed_value()
        except (ValueError, TypeError, json.JSONDecodeError):
            return obj.value
    
    def validate_key(self, value):
        """Valida se a chave não contém caracteres especiais"""
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise serializers.ValidationError(
                "A chave deve conter apenas letras, números, pontos, hífens e underscores."
            )
        return value


class SettingTemplateSerializer(serializers.ModelSerializer):
    typed_default_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SettingTemplate
        fields = [
            'id', 'key', 'name', 'description', 'setting_type', 'default_value',
            'typed_default_value', 'category', 'scope', 'is_required', 'is_public',
            'validation_rules', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_typed_default_value(self, obj):
        """Retorna o valor padrão convertido para o tipo correto"""
        if not obj.default_value:
            return None
        
        try:
            if obj.setting_type == 'integer':
                return int(obj.default_value)
            elif obj.setting_type == 'float':
                return float(obj.default_value)
            elif obj.setting_type == 'boolean':
                return obj.default_value.lower() in ('true', '1', 'yes', 'on')
            elif obj.setting_type == 'json':
                import json
                return json.loads(obj.default_value)
            return obj.default_value
        except (ValueError, TypeError, json.JSONDecodeError):
            return obj.default_value
    
    def validate_key(self, value):
        """Valida se a chave não contém caracteres especiais"""
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise serializers.ValidationError(
                "A chave deve conter apenas letras, números, pontos, hífens e underscores."
            )
        return value


class SettingValueSerializer(serializers.Serializer):
    """Serializer para atualizar apenas o valor de uma configuração"""
    value = serializers.CharField()
    
    def validate_value(self, value):
        """Valida o valor baseado no tipo da configuração"""
        setting = self.context.get('setting')
        if not setting:
            return value
        
        try:
            if setting.setting_type == 'integer':
                int(value)
            elif setting.setting_type == 'float':
                float(value)
            elif setting.setting_type == 'boolean':
                if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                    raise serializers.ValidationError(
                        "Valor booleano deve ser: true/false, 1/0, yes/no, on/off"
                    )
            elif setting.setting_type == 'json':
                import json
                json.loads(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise serializers.ValidationError(
                f"Valor inválido para o tipo {setting.setting_type}: {str(e)}"
            )
        
        return value


class BulkSettingsSerializer(serializers.Serializer):
    """Serializer para atualizar múltiplas configurações de uma vez"""
    settings = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dicionário com chave-valor das configurações"
    )
    
    def validate_settings(self, value):
        """Valida se todas as chaves são válidas"""
        import re
        for key in value.keys():
            if not re.match(r'^[a-zA-Z0-9_.-]+$', key):
                raise serializers.ValidationError(
                    f"Chave '{key}' inválida. Deve conter apenas letras, números, pontos, hífens e underscores."
                )
        return value