from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Producto, Proveedor, Rack, Area,
    Recepcion, RecepcionItem,
    Despacho, DespachoItem
)

# ==============================================================================
# Formularios para Catálogos (Producto, Proveedor, Rack, Area)
# ==============================================================================

class ProductoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    class Meta:
        model = Producto
        fields = [
            'codigo_producto', 'nombre', 'cantidad_stock', 'stock_minimo',
            'ubicacion_rack', 'proveedor', 'categoria', 'estado',
            'unidad_de_medida', 'observaciones',
        ]

class ProveedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono', 'correo_electronico']

class RackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Rack
        fields = ['codigo_rack', 'descripcion']

class AreaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Area
        fields = ['nombre', 'descripcion']

# ==============================================================================
# Formularios para Movimientos (Recepción y Despacho)
# ==============================================================================

class RecepcionForm(forms.ModelForm):
    class Meta:
        model = Recepcion
        fields = ['proveedor', 'documento_referencia']
        widgets = {
            'proveedor': forms.Select(attrs={
                'class': 'form-select',
            }),
            'documento_referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: OC-12345'
            }),
        }

class RecepcionItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RecepcionItem
        fields = ['producto', 'cantidad']

ItemRecepcionFormSet = forms.inlineformset_factory(
    Recepcion, RecepcionItem, form=RecepcionItemForm, extra=1, can_delete=False
)

class DespachoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
    class Meta:
        model = Despacho
        fields = ['usuario_solicitante', 'area', 'motivo']

class DespachoItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = DespachoItem
        fields = ['producto', 'cantidad']

ItemDespachoFormSet = forms.inlineformset_factory(
    Despacho, DespachoItem, form=DespachoItemForm, extra=1, can_delete=False
)

# ==============================================================================
# Formularios para Gestión de Usuarios
# ==============================================================================

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

class CustomUserChangeForm(forms.ModelForm):
    """Formulario para editar los datos básicos de un usuario y sus grupos."""
    class Meta:
        model = User
        fields = ('username', 'email', 'groups', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].widget = forms.CheckboxSelectMultiple()
        self.fields['groups'].queryset = Group.objects.all()
        self.fields['groups'].label = "Roles"
        for field in self.fields:
            if field != 'is_active':
                self.fields[field].widget.attrs.update({'class': 'form-control'})