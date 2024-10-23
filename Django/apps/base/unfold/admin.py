from typing import Any, Sequence
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _
from datetime import datetime as dt
from django.contrib import messages
from apps.base.models import BaseModel

class UnfoldModelAdmin(ModelAdmin):
    """
    Base admin class for all models using Django Unfold.
    
    This class extends the functionality of Django Unfold's ModelAdmin to provide
    consistent handling of audit fields (created_date, modified_date, deleted_date, changed_by)
    across all admin interfaces that inherit from it.
    
    Features:
    - Automatically adds audit fields when editing existing objects
    - Handles the 'changed_by' field automatically on save
    - Implements a soft delete functionality
    """
    
    # Define audit fields
    audit_fields = ('status', 'created_date', 'modified_date', 'deleted_date', 'changed_by')
    prefetch_related:Sequence[str] = ()
    
    @property
    def prefetch_related_fields(self) -> Sequence[str]:
        if isinstance(self.prefetch_related, list) or isinstance(self.prefetch_related, tuple):
            return self.prefetch_related
        
        messages.warning(self.request, "prefetch_related must be a sequence of strings")
        return ()
    
    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.prefetch_related(*self.prefetch_related_fields)
    
    def get_audit_fieldset(self, request, obj=None):
        """
        Returns the audit fieldset if the model has audit fields.
        """
        if obj and any(hasattr(obj, field) for field in self.audit_fields):
            return (_('Audit Information'), {
                'fields': [field for field in self.audit_fields if hasattr(obj, field)],
                'classes': ('collapse',)
            })
        return None

    def get_fieldsets(self, request, obj=None):
        """
        Adds the audit fieldset to the existing fieldsets when editing an object.
        Removes audit fields from the default fieldset to avoid duplication.
        """
        fieldsets = super().get_fieldsets(request, obj)
        if fieldsets is None:
            # Si no hay fieldsets definidos, creamos uno con todos los campos excepto los de auditoría
            all_fields = self.get_fields(request, obj)
            non_audit_fields = [f for f in all_fields if f not in self.audit_fields]
            fieldsets = [(None, {'fields': non_audit_fields})]
        else:
            # Si hay fieldsets definidos, removemos los campos de auditoría de ellos
            fieldsets = list(fieldsets)
            for name, options in fieldsets:
                if 'fields' in options:
                    options['fields'] = [f for f in options['fields'] if f not in self.audit_fields]

        audit_fieldset = self.get_audit_fieldset(request, obj)
        if audit_fieldset:
            fieldsets.append(audit_fieldset)
        
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        """
        Adds audit fields to readonly_fields when editing an existing object.
        """
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # editing an existing object
            readonly_fields.extend([field for field in self.audit_fields if hasattr(obj, field)])
        return readonly_fields

    def save_model(self, request, obj, form, change):
        """
        Automatically sets the 'changed_by' field to the current user when saving.
        """
        if hasattr(obj, 'changed_by'):
            obj.changed_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj:BaseModel):
        """
        Implements soft delete functionality if the model has 'status' and 'deleted_date' fields.
        """
        if hasattr(obj, 'status') and hasattr(obj, 'deleted_date'):
            obj.status = obj.deactivated_status
            obj.deleted_date = dt.now()
            if hasattr(obj, 'changed_by'):
                obj.changed_by = request.user
            obj.save()
        else:
            super().delete_model(request, obj)

    def save_formset(self, request, form, formset, change):
        """
        Handles the 'changed_by' field for inline forms (formsets).
        """
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, 'changed_by'):
                instance.changed_by = request.user
            instance.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            if hasattr(obj, 'status') and hasattr(obj, 'deleted_date'):
                obj.status = obj.deactivated_status
                obj.deleted_date = dt.now()
                if hasattr(obj, 'changed_by'):
                    obj.changed_by = request.user
                obj.save()
            else:
                obj.delete()

class UnfoldModelAdminWithManualStatus(UnfoldModelAdmin):
    """
    Admin class for models that require manual status management.
    
    This class extends UnfoldModelAdmin but allows the 'status' field
    to be manually edited in the admin interface.
    """
    def get_readonly_fields(self, request, obj=None):
        """
        Removes 'status' from readonly fields to allow manual editing.
        """
        readonly_fields = super().get_readonly_fields(request, obj)
        return [f for f in readonly_fields if f != 'status']

    def get_exclude(self, request, obj=None):
        """
        Ensures 'status' is not excluded from the admin form.
        """
        exclude = super().get_exclude(request, obj)
        if exclude and 'status' in exclude:
            exclude.remove('status')
        return exclude
