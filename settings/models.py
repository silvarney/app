from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from accounts.models import Account
import json

User = get_user_model()


class GlobalSetting(models.Model):
    """Configurações globais do sistema"""
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('text', 'Text'),
    ]
    
    key = models.CharField(max_length=100, unique=True, help_text="Chave única da configuração")
    value = models.TextField(help_text="Valor da configuração")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True, help_text="Descrição da configuração")
    category = models.CharField(max_length=50, blank=True, help_text="Categoria da configuração")
    is_public = models.BooleanField(default=False, help_text="Se a configuração pode ser acessada publicamente")
    is_editable = models.BooleanField(default=True, help_text="Se a configuração pode ser editada")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'settings_global'
        verbose_name = 'Configuração Global'
        verbose_name_plural = 'Configurações Globais'
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"
    
    def get_typed_value(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'json':
            return json.loads(self.value)
        return self.value
    
    def set_typed_value(self, value):
        """Define o valor convertendo para string"""
        if self.setting_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)


class AccountSetting(models.Model):
    """Configurações específicas por conta"""
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('text', 'Text'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='settings')
    key = models.CharField(max_length=100, help_text="Chave da configuração")
    value = models.TextField(help_text="Valor da configuração")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True, help_text="Descrição da configuração")
    category = models.CharField(max_length=50, blank=True, help_text="Categoria da configuração")
    is_inherited = models.BooleanField(default=False, help_text="Se herda valor da configuração global")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'settings_account'
        verbose_name = 'Configuração da Conta'
        verbose_name_plural = 'Configurações das Contas'
        unique_together = ['account', 'key']
        ordering = ['account', 'category', 'key']
    
    def __str__(self):
        return f"{self.account.name} - {self.key}: {self.value[:50]}"
    
    def get_typed_value(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'json':
            return json.loads(self.value)
        return self.value
    
    def set_typed_value(self, value):
        """Define o valor convertendo para string"""
        if self.setting_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)


class UserSetting(models.Model):
    """Configurações específicas por usuário"""
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('text', 'Text'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settings')
    key = models.CharField(max_length=100, help_text="Chave da configuração")
    value = models.TextField(help_text="Valor da configuração")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True, help_text="Descrição da configuração")
    category = models.CharField(max_length=50, blank=True, help_text="Categoria da configuração")
    is_inherited = models.BooleanField(default=False, help_text="Se herda valor da configuração da conta")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'settings_user'
        verbose_name = 'Configuração do Usuário'
        verbose_name_plural = 'Configurações dos Usuários'
        unique_together = ['user', 'key']
        ordering = ['user', 'category', 'key']
    
    def __str__(self):
        return f"{self.user.email} - {self.key}: {self.value[:50]}"
    
    def get_typed_value(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'json':
            return json.loads(self.value)
        return self.value
    
    def set_typed_value(self, value):
        """Define o valor convertendo para string"""
        if self.setting_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)


class SettingTemplate(models.Model):
    """Templates de configurações para facilitar a criação"""
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('text', 'Text'),
    ]
    
    SCOPE_CHOICES = [
        ('global', 'Global'),
        ('account', 'Conta'),
        ('user', 'Usuário'),
    ]
    
    key = models.CharField(max_length=100, unique=True, help_text="Chave da configuração")
    name = models.CharField(max_length=200, help_text="Nome amigável da configuração")
    description = models.TextField(help_text="Descrição da configuração")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    default_value = models.TextField(blank=True, help_text="Valor padrão")
    category = models.CharField(max_length=50, help_text="Categoria da configuração")
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, help_text="Escopo da configuração")
    is_required = models.BooleanField(default=False, help_text="Se a configuração é obrigatória")
    is_public = models.BooleanField(default=False, help_text="Se pode ser acessada publicamente")
    validation_rules = models.JSONField(blank=True, null=True, help_text="Regras de validação em JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'settings_template'
        verbose_name = 'Template de Configuração'
        verbose_name_plural = 'Templates de Configurações'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.scope})"
