from django import forms
from django.db.models import Max
from site_management.models import (
    SiteCategory, Service, SocialNetwork, CTA, BlogPost, Site
)


class UserPanelBaseForm(forms.ModelForm):
    """Base para filtrar sites acessíveis ao usuário (owner/admin/member ativo)."""
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Padroniza estilo de selects e uploads para terem cantos arredondados como os inputs de texto
        for fname, field in self.fields.items():
            w = field.widget
            # Selects
            if isinstance(w, forms.Select):
                base_cls = 'w-full border rounded-md px-3 py-2 bg-white'
                existing = w.attrs.get('class', '')
                if 'rounded-md' not in existing:
                    w.attrs['class'] = (existing + ' ' + base_cls).strip()
            # File inputs
            if isinstance(w, forms.ClearableFileInput):
                base_cls = 'w-full border rounded-md px-3 py-2 bg-white cursor-pointer'
                existing = w.attrs.get('class', '')
                if 'rounded-md' not in existing:
                    w.attrs['class'] = (existing + ' ' + base_cls).strip()
        if 'site' in self.fields:
            if user and user.is_authenticated:
                self.fields['site'].queryset = Site.objects.filter(
                    account__memberships__user=user,
                    account__memberships__status='active'
                ).distinct()
            self.fields['site'].empty_label = 'Selecione um site'


class SiteCategoryForm(UserPanelBaseForm):
    class Meta:
        model = SiteCategory
        # 'order' removido do formulário; será atribuído automaticamente
        fields = ['site', 'name', 'icon', 'image', 'is_active']
        labels = {
            'site': 'Site',
            'name': 'Nome',
            'icon': 'Ícone',
            'image': 'Imagem',
            'is_active': 'Ativo'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            'icon': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2', 'placeholder': 'ex: fa-solid fa-star'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
        }

    def clean(self):
        cleaned = super().clean()
        site = cleaned.get('site')
        name = cleaned.get('name')
        # Validar duplicidade com mensagem amigável (case-insensitive)
        if site and name:
            qs = SiteCategory.objects.filter(site=site, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('name', 'Já existe uma categoria com este nome para o site selecionado.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Atribuir ordem automática somente em criação
        if not instance.pk:
            max_order = SiteCategory.objects.filter(site=instance.site).aggregate(m=Max('order'))['m']
            instance.order = (max_order or 0) + 1
        if commit:
            instance.save()
        return instance


class ServiceForm(UserPanelBaseForm):
    class Meta:
        model = Service
        # order será definido automaticamente na criação; 'link' incluído se existir no schema
        fields = ['site', 'category', 'title', 'subtitle', 'description', 'image', 'value', 'discount', 'is_active']
        labels = {
            'site': 'Site',
            'category': 'Categoria',
            'title': 'Título',
            'subtitle': 'Subtítulo',
            'description': 'Descrição',
            'image': 'Imagem',
            'value': 'Valor',
            'discount': 'Desconto (%)',
            'is_active': 'Ativo'
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            'subtitle': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            'description': forms.Textarea(attrs={'class': 'w-full border rounded-md px-3 py-2', 'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'value': forms.NumberInput(attrs={'class': 'w-full border rounded-md px-3 py-2', 'step': '0.01', 'min': '0'}),
            'discount': forms.NumberInput(attrs={'class': 'w-full border rounded-md px-3 py-2', 'step': '0.01', 'min': '0', 'max': '100'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.get('user') or kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            # Filtra categorias de sites do usuário
            self.fields['category'].queryset = self.fields['category'].queryset.filter(
                site__account__memberships__user=user,
                site__account__memberships__status='active'
            ).distinct()

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Garante subtítulo preenchido para bancos com NOT NULL mesmo se campo não exibido (fallback)
        if hasattr(instance, 'subtitle') and not instance.subtitle:
            instance.subtitle = instance.title[:255]
        if not instance.pk:
            from django.db.models import Max
            max_order = Service.objects.filter(site=instance.site).aggregate(m=Max('order'))['m']
            instance.order = (max_order or 0) + 1
        # Preencher link se campo existir e estiver vazio (evita IntegrityError em bancos com constraint)
        if hasattr(instance, 'link') and not getattr(instance, 'link'):
            # gera slug simples baseado no título
            from django.utils.text import slugify
            base = slugify(instance.title)[:40] or 'servico'
            setattr(instance, 'link', f"/{base}/")
        if commit:
            instance.save()
        return instance


class SocialNetworkForm(UserPanelBaseForm):
    class Meta:
        model = SocialNetwork
        fields = ['site', 'network_type', 'url', 'icon_style', 'is_active']
        labels = {
            'site': 'Site',
            'network_type': 'Tipo',
            'url': 'URL',
            'icon_style': 'Estilo do Ícone',
            'is_active': 'Ativo'
        }
        widgets = {
            'url': forms.URLInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
        }


class CTAForm(UserPanelBaseForm):
    class Meta:
        model = CTA
        fields = ['site', 'image', 'title', 'description', 'action_type', 'button_text', 'order', 'is_active']
        labels = {
            'site': 'Site',
            'image': 'Imagem',
            'title': 'Título',
            'description': 'Descrição',
            'action_type': 'Ação do Botão',
            'button_text': 'Texto do Botão',
            'order': 'Ordem',
            'is_active': 'Ativo'
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            'description': forms.Textarea(attrs={'class': 'w-full border rounded-md px-3 py-2', 'rows': 4}),
            'button_text': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'order': forms.NumberInput(attrs={'class': 'w-full border rounded-md px-3 py-2', 'min': '0'}),
        }


class BlogPostForm(UserPanelBaseForm):
    class Meta:
        model = BlogPost
        # status substitui is_published (publicar ou rascunho) – manteremos campo is_published mas expomos via select lógico
        fields = ['site', 'title', 'image', 'video_url', 'content', 'link', 'category', 'tags', 'is_published']
        labels = {
            'site': 'Site',
            'title': 'Título',
            'image': 'Imagem',
            'video_url': 'URL Vídeo',
            'content': 'Texto',  # será WYSIWYG
            'link': 'Link',
            'category': 'Categoria',
            'tags': 'Tags',
            'is_published': 'Status'
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            'video_url': forms.URLInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            'link': forms.URLInput(attrs={'class': 'w-full border rounded-md px-3 py-2'}),
            # placeholder: será substituído via JS por editor (ex: Quill ou TinyMCE) – mantendo textarea para fallback
            'content': forms.Textarea(attrs={'class': 'w-full border rounded-md px-3 py-2 js-richtext', 'rows': 14}),
            # tags com datalist para sugestões existentes (separadas por vírgula)
            'tags': forms.TextInput(attrs={'class': 'w-full border rounded-md px-3 py-2 js-tags-input', 'placeholder': 'tag1, tag2'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.get('user') or kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Filtra categorias dinamicamente pelo site selecionado (POST/GET) ou instance
        from site_management.models import SiteCategory
        site_selected = None
        if self.data.get('site'):
            try:
                site_selected = int(self.data.get('site'))
            except (TypeError, ValueError):
                site_selected = None
        elif self.initial.get('site'):
            site_selected = getattr(self.initial.get('site'), 'id', self.initial.get('site'))
        elif self.instance and self.instance.pk:
            site_selected = self.instance.site_id

        base_qs = SiteCategory.objects.none()
        if user and user.is_authenticated:
            base_qs = SiteCategory.objects.filter(
                site__account__memberships__user=user,
                site__account__memberships__status='active',
                is_blog=True
            )
        if site_selected:
            base_qs = base_qs.filter(site_id=site_selected)
        self.fields['category'].queryset = base_qs.order_by('order','name')
        # Especificação define título obrigatório
        self.fields['title'].required = True
        # Ajusta choices para status publicar/rascunho via field is_published (True/False)
        self.fields['is_published'].widget = forms.Select(choices=[(True, 'Publicar'), (False, 'Rascunho')], attrs={'class': 'w-full border rounded-md px-3 py-2'})

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        # normaliza espaços duplicados e vírgulas
        cleaned = ', '.join(filter(None, [t.strip() for t in tags.replace(';', ',').split(',')]))
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # published_at coerente
        if instance.is_published and not instance.published_at:
            from django.utils import timezone
            instance.published_at = timezone.now()
        if not instance.is_published:
            instance.published_at = None
        if commit:
            instance.save()
        return instance
