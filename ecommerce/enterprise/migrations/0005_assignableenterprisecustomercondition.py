# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-29 21:02
from __future__ import absolute_import, unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise', '0004_add_enterprise_offers_for_coupons'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignableEnterpriseCustomerCondition',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('enterprise.enterprisecustomercondition',),
        ),
    ]