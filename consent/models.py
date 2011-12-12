"""
There are two key models in the Consent app. These are Privilege and Consent. A
privilage is added to the website normally in the Django admin and then a user
has the option of granting the consent to to the website. After Consent has
been granted, the user is able to revoke the consent.
"""
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User


class Privilege(models.Model):
    """
    A privilage is a permission that the website asks from the user. This could
    be the permission to email them, share the users details or to use their
    (already authorised) social netorking sites.
    """
    name = models.CharField(max_length=64)
    description = models.TextField()
    users = models.ManyToManyField(User, through='consent.Consent')

    class Meta:
        ordering = ['name', ]

    def __unicode__(self):
        return self.name


class ConsentManager(models.Manager):

    def for_user(self, user):
        return Consent.objects.filter(user=user)

    def grant_consent(self, user, privileges):
        for privilege in privileges:
            consent, created = Consent.objects.get_or_create(
                user=user, privilege=privilege)
            if not created:
                consent.revoked = False
                consent.revoked_on = None
                consent.save()

    def revoke_consent(self, user, privileges):
        Consent.objects.filter(user=user, privilege__in=privileges).update(
                revoked=True, revoked_on=datetime.now())

    def granted(self, user=None):
        granted_consents = self.filter(revoked=False)
        if user:
            granted_consents = granted_consents.filter(user=user)
        return granted_consents

    def revoked(self, user=None):
        revoked_consents = self.filter(revoked=True)
        if user:
            revoked_consents = revoked_consents.filter(user=user)
        return revoked_consents


class Consent(models.Model):
    """
    Consent is the agreement from a user to grant a specific privilege. This can
    then be revoked by the user at a later date.
    """
    user = models.ForeignKey(User)
    privilege = models.ForeignKey(Privilege)
    granted_on = models.DateTimeField(default=datetime.now)
    revoked_on = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    objects = ConsentManager()

    class Meta:
        unique_together = ('user', 'privilege',)

    def revoke(self):
        """
        Revoke the users consent for the Privilege if it has not already been
        revoked.
        """
        if not self.revoked:
            self.revoked = True
            self.revoked_on = datetime.now()

    def grant(self):
        """
        Grant the users consent for the Privilege if it has been revoked.
        """
        if self.revoked:
            self.revoked = False
            self.revoked_on = None
            self.granted_on = datetime.now()

    def __unicode__(self):

        if self.revoked:
            adjv = 'permits'
        else:
            adjv = 'revoked'

        return "%s %s the '%s' privilege" % (self.user, adjv, self.privilege)
