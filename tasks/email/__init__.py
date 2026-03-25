from .mailtm import MailTmProvider, MailTmTask
from .guerrillamail import GuerrillaMailProvider, GuerrillaMailTask
from .getnada import GetNadaProvider, GetNadaTask
from .yopmail import YopMailProvider, YopMailTask
from .outlook import OutlookRegister, OutlookMailClient
from .gmail import GmailClient, GmailIMAPTask
from .tempmail import TempMailConverter, TenMinuteMailTask
from .onemail import OneSecMailProvider, OneSecMailTask
from .tempmail_org import TempMailOrgProvider, TempMailOrgTask
from .gmailnator import GmailnatorProvider, GmailnatorTask
from .fakemail import FakeMailProvider, FakeMailTask
from .fakemail_cloudflare import FakeMailCloudflareProvider, FakeMailCloudflareTask
from .selfhosted import SelfHostedMailProvider, SelfHostedMailTask

__all__ = [
    'MailTmProvider',
    'MailTmTask',
    'GuerrillaMailProvider', 
    'GuerrillaMailTask',
    'GetNadaProvider',
    'GetNadaTask',
    'YopMailProvider',
    'YopMailTask',
    'OutlookRegister',
    'OutlookMailClient',
    'GmailClient',
    'GmailIMAPTask',
    'TempMailConverter',
    'TenMinuteMailTask',
    'OneSecMailProvider',
    'OneSecMailTask',
    'TempMailOrgProvider',
    'TempMailOrgTask',
    'GmailnatorProvider',
    'GmailnatorTask',
    'FakeMailProvider',
    'FakeMailTask',
    'FakeMailCloudflareProvider',
    'FakeMailCloudflareTask',
    'SelfHostedMailProvider',
    'SelfHostedMailTask'
]
