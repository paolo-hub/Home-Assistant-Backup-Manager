"""Run the shipped YAML in HA 2026.9.4; only BMA/provider I/O is simulated."""
from __future__ import annotations
import asyncio
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
import pytest_asyncio
import yaml
from homeassistant.core import HomeAssistant, SupportsResponse, CoreState
from homeassistant.setup import async_setup_component
from homeassistant import loader, bootstrap
from homeassistant.config import merge_packages_config, _recursive_merge
from homeassistant.helpers.selector import validate_selector
import voluptuous as vol
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import template

ROOT = Path(__file__).resolve().parents[1]
class Loader(yaml.SafeLoader):
    pass
Loader.add_constructor('!secret', lambda loader, node: 'test-only-password')

def load_package():
    return yaml.load((ROOT/'package/pkg_backup_home_assistant.yaml').read_text(), Loader=Loader)

async def package_config(hass):
    """Exercise the same package merge used by HA's YAML configuration loader."""
    packages = {'bma_backup': load_package()}
    config = {'homeassistant': {'packages': packages}}
    errors = []
    await merge_packages_config(hass, config, packages,
                                _log_pkg_error=lambda *args: errors.append(args[-1]))
    assert not errors, errors
    return config

@pytest_asyncio.fixture
async def env(tmp_path):
    (tmp_path/'configuration.yaml').write_text('{}\n')
    hass = HomeAssistant(str(tmp_path))
    hass.config.time_zone = 'Europe/Rome'
    hass.config.skip_pip = True
    loader.async_setup(hass)
    config = await package_config(hass)
    calls=[]; notices=[]; reports=[]
    state={'agents':{'hassio.local':{'name':'Local','domain':'hassio'}},'errors':{},'state':'idle','create_error':False,'bad_response':False,'apply_error':False,'hold':None}
    async def refresh(call):
        calls.append(('refresh',dict(call.data)))
        return {'agents':state['agents'],'agent_errors':state['errors'],'state':state['state'],'inventory_complete':not state['errors']}
    async def create(call):
        calls.append(('create',dict(call.data)))
        if state['hold'] is not None:
            await state['hold'].wait()
        if state['create_error']:
            raise HomeAssistantError('Simulated partial provider/content failure')
        if state['bad_response']:
            return {}
        result={'backup_id':f'test-{len(calls)}','name':call.data['name'],'date':'2026-10-04T12:00:00+00:00','source_type':'bma','job_id':call.data['job_id'],'stored_agent_ids':list(call.data['agent_ids']),'failed_agent_ids':[],'failed_addons':[],'failed_folders':[]}
        hass.bus.async_fire('backup_manager_actions_backup_created',result | {'agent_ids':result['stored_agent_ids']})
        return result
    def plan(data):
        return {'evaluated_at':'2026-10-04T12:00:00+00:00','scope':{'source_type':data['source_type'],'job_id':data.get('job_id'),'group_by':data.get('group_by'),'agent_ids':data['agent_ids']},'summary':{'considered':5,'keep':3,'delete':2,'out_of_scope':4,'reclaimable_size_bytes':12345,'reclaimable_size_complete':True},'keep':[],'delete':[]}
    async def retention(call):
        calls.append((call.service,dict(call.data)))
        if call.service == 'apply_retention':
            if state['apply_error']:raise HomeAssistantError('Simulated failure after one deletion')
            return {'plan':plan(call.data),'execution':{'deleted_count':2,'already_absent_count':0,'deleted':[]}}
        return plan(call.data)
    async def notify(call):notices.append(dict(call.data))
    for name,fn in [('refresh',refresh),('create',create),('plan_retention',retention),('apply_retention',retention)]:
        hass.services.async_register('backup_manager_actions',name,fn,supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register('notify','pushover_hassio',notify)
    hass.bus.async_listen('bma_backup_report',lambda event:reports.append(dict(event.data)))
    # Setup genuine HA integrations. There is no Supervisor, provider, or real backup manager.
    assert await bootstrap.async_from_config_dict(config, hass) is hass
    await hass.async_block_till_done()
    for domain in ['input_boolean','input_number','input_select','input_datetime','script','template','automation']:
        assert domain in hass.config.components, domain
    hass.states.async_set('sensor.destinazioni_backup','1',{'agents':state['agents'],'agent_errors':state['errors']})
    await hass.async_start()
    await hass.async_block_till_done()
    yield SimpleNamespace(hass=hass,calls=calls,state=state,notices=notices,reports=reports,config=config)
    await hass.async_stop(force=True)

async def invoke(e,script,**data):
    await e.hass.services.async_call('script','bma_backup_'+script,data,blocking=True)
    await e.hass.async_block_till_done()

async def toggle(e,key,on=True):
    await e.hass.services.async_call('input_boolean','turn_on' if on else 'turn_off',{'entity_id':'input_boolean.bma_backup_'+key},blocking=True)
    await e.hass.async_block_till_done()

@pytest.mark.asyncio
async def test_initialization_and_partial(env):
    e=env
    assert e.hass.states.get('input_boolean.bma_backup_initialized').state=='on'
    await invoke(e,'run_partial')
    creates=[d for k,d in e.calls if k=='create']
    assert len(creates)==1
    assert creates[0]['job_id']=='partial'
    assert creates[0]['agent_ids']==['hassio.local']
    assert creates[0]['include_homeassistant'] is True
    assert creates[0]['include_database'] is True
    assert creates[0]['include_all_addons'] is False
    assert creates[0]['include_folders']==[]
    assert e.hass.states.get('sensor.bma_backup_status').state=='success'
    assert not any(k=='apply_retention' for k,d in e.calls)

@pytest.mark.asyncio
async def test_full_local_and_password(env):
    await toggle(env,'use_password')
    await invoke(env,'run_full')
    c=next(d for k,d in env.calls if k=='create')
    assert c['job_id']=='full'
    assert c['include_all_addons'] is True
    assert c['include_folders']==['addons/local','media','share','ssl']
    assert c['password']=='test-only-password'
    assert 'test-only-password' not in str(env.notices)+str(env.reports)

@pytest.mark.asyncio
@pytest.mark.parametrize('case',['none','unmapped','absent','error','busy','unknown_selector','create_failure','invalid_response'])
async def test_fail_closed(env,case):
    e=env
    if case=='none':await toggle(e,'destination_partial_local',False)
    if case=='unmapped':
        e.hass.states.async_set('input_boolean.bma_backup_destination_partial_unconfigured','on',{'agent_id':''})
    if case=='absent':e.state['agents']={}
    if case=='error':e.state['errors']={'hassio.local':'offline'}
    if case=='busy':e.state['state']='creating_backup'
    if case=='unknown_selector':e.hass.states.async_set('input_boolean.bma_backup_destination_partial_local','unavailable',{'agent_id':'hassio.local'})
    if case=='create_failure':e.state['create_error']=True
    if case=='invalid_response':e.state['bad_response']=True
    await invoke(e,'run_partial')
    await e.hass.async_block_till_done()
    assert not any(k=='apply_retention' for k,d in e.calls)
    if case not in ['create_failure','invalid_response']:assert not any(k=='create' for k,d in e.calls)
    assert e.hass.states.get('sensor.bma_backup_status').state=='failed'
    assert e.notices

@pytest.mark.asyncio
async def test_unselected_error_does_not_block_local(env):
    env.state['errors']={'s3.not_selected':'offline'}
    await invoke(env,'run_partial')
    assert any(k=='create' for k,d in env.calls)

@pytest.mark.asyncio
@pytest.mark.parametrize('job',['full','partial'])
async def test_dry_run(env,job):
    await env.hass.services.async_call('input_select','select_option',{'entity_id':'input_select.bma_backup_retention_profile','option':job},blocking=True)
    await invoke(env,'plan_retention')
    c=next(d for k,d in env.calls if k=='plan_retention')
    assert c['source_type']=='bma' and c['job_id']==job and c['agent_ids']==['hassio.local']
    assert c['keep_last']==3 and c['daily']==0
    s=env.hass.states.get('sensor.bma_backup_retention_plan')
    assert s.attributes['summary']['delete']==2
    assert s.attributes['summary']['reclaimable_size_complete'] is True
    assert not any(k=='apply_retention' for k,d in env.calls)

@pytest.mark.asyncio
async def test_apply_locked_then_simulated(env):
    await invoke(env,'apply_retention')
    assert not any(k=='apply_retention' for k,d in env.calls)
    await toggle(env,'apply_unlocked')
    await invoke(env,'apply_retention')
    assert sum(k=='apply_retention' for k,d in env.calls)==1
    assert env.hass.states.get('sensor.bma_backup_retention_apply').attributes['execution']['deleted_count']==2
    assert not any(k=='plan_retention' for k,d in env.calls)

@pytest.mark.asyncio
async def test_partial_apply_failure_preserves_actual_report(env):
    await toggle(env,'apply_unlocked')
    await invoke(env,'apply_retention')
    before=env.hass.states.get('sensor.bma_backup_retention_apply')
    env.state['apply_error']=True
    await invoke(env,'apply_retention')
    await env.hass.async_block_till_done()
    assert env.hass.states.get('sensor.bma_backup_retention_apply').attributes==before.attributes
    assert env.hass.states.get('sensor.bma_backup_status').state=='failed'

@pytest.mark.asyncio
async def test_initializer_does_not_reset_choices(env):
    await toggle(env,'full_include_media',False)
    await invoke(env,'initialize')
    assert env.hass.states.get('input_boolean.bma_backup_full_include_media').state=='off'

@pytest.mark.asyncio
@pytest.mark.parametrize('job',['full','partial'])
async def test_scheduler_disabled(env,job):
    # Execute the actual automation with condition checking, not skip_condition's default.
    await env.hass.services.async_call('automation','trigger',{'entity_id':'automation.bma_backup_'+job+'_scheduler','skip_condition':False},blocking=True)
    await env.hass.async_block_till_done()
    assert not any(k=='create' for k,d in env.calls)

@pytest.mark.asyncio
@pytest.mark.parametrize('source,job,expected',[('bma','full',True),('bma','partial',True),('ha_native',None,True),('app_update',None,True),('unknown',None,False),('bma','other',False)])
async def test_event_dispatch(env,source,job,expected):
    profile=job if source=='bma' else source
    for p in ['full','partial','ha_native','app_update']:
        await toggle(env,p+'_retention_enabled')
        await toggle(env,'destination_'+p+'_local')
    await toggle(env,'apply_unlocked')
    env.hass.bus.async_fire('backup_manager_actions_backup_created',{'backup_id':'external-test','source_type':source,'job_id':job,'agent_ids':['hassio.local'],'failed_agent_ids':[],'name':'Example','date':'2026-10-04','app_slug':'test_app'})
    await env.hass.async_block_till_done()
    c=[d for k,d in env.calls if k=='apply_retention']
    assert len(c)==int(expected)
    if expected:
        assert c[0]['agent_ids']==['hassio.local']
        if source=='bma':assert c[0]['job_id']==job
        else:assert 'job_id' not in c[0]
        if source=='app_update':assert c[0]['group_by']=='app'

@pytest.mark.asyncio
async def test_health_selected_scope_and_transitions(env):
    e=env
    await toggle(e,'full_enabled')
    await asyncio.sleep(1.1)
    await e.hass.async_block_till_done()
    assert e.hass.states.get('binary_sensor.bma_backup_required_destinations_ready').state=='on'
    async def set_errors(errors):
        e.hass.states.async_set('sensor.destinazioni_backup','1',{'agents':e.state['agents'],'agent_errors':errors})
        await e.hass.async_block_till_done()
        # Domain-wide discovery uses HA's automatic rate limiting.
        await asyncio.sleep(1.1)
        await e.hass.async_block_till_done()
    await set_errors({'other':'offline'})
    assert e.hass.states.get('binary_sensor.bma_backup_required_destinations_ready').state=='on'
    await set_errors({'hassio.local':'offline'})
    assert e.hass.states.get('binary_sensor.bma_backup_required_destinations_ready').state=='off'
    await set_errors({})
    assert e.hass.states.get('binary_sensor.bma_backup_required_destinations_ready').state=='on'
    assert any('recovered' in n['message'] for n in e.notices)

@pytest.mark.asyncio
async def test_dynamic_destination_without_runner_change(env):
    env.state['agents']['new.provider']={'name':'new'}
    env.hass.states.async_set('input_boolean.bma_backup_destination_partial_future','on',{'agent_id':'new.provider'})
    await invoke(env,'run_partial')
    c=next(d for k,d in env.calls if k=='create')
    assert c['agent_ids']==['hassio.local','new.provider']

@pytest.mark.asyncio
async def test_changed_event_scope_blocks_retention(env):
    await toggle(env,'apply_unlocked')
    await toggle(env,'partial_retention_enabled')
    env.hass.states.async_set('input_boolean.bma_backup_destination_partial_new','on',{'agent_id':'other'})
    await invoke(env,'worker',operation='apply',job='partial',automatic=True,event_agents=['hassio.local'])
    assert not any(k=='apply_retention' for k,d in env.calls)

@pytest.mark.asyncio
async def test_encryption_unknown_fails_closed(env):
    env.hass.states.async_set('input_boolean.bma_backup_use_password','unavailable')
    await invoke(env,'run_partial')
    assert not any(k=='create' for k,d in env.calls)
    assert env.hass.states.get('sensor.bma_backup_status').state=='failed'

@pytest.mark.asyncio
async def test_full_partial_and_event_retention_serialize(env):
    e=env
    await toggle(e,'apply_unlocked')
    await toggle(e,'full_retention_enabled')
    e.state['hold']=asyncio.Event()
    first=asyncio.create_task(invoke(e,'run_full'))
    for _ in range(100):
        if any(k=='create' for k,d in e.calls):break
        await asyncio.sleep(0.01)
    assert sum(k=='create' for k,d in e.calls)==1
    second=asyncio.create_task(invoke(e,'run_partial'))
    duplicate=asyncio.create_task(invoke(e,'run_full'))
    await asyncio.sleep(0.05)
    assert sum(k=='create' for k,d in e.calls)==1
    e.state['hold'].set()
    await asyncio.wait_for(asyncio.gather(first,second,duplicate),10)
    assert [d['job_id'] for k,d in e.calls if k=='create']==['full','partial']
    assert sum(k=='apply_retention' for k,d in e.calls)==1

@pytest.mark.asyncio
async def test_real_restore_no_replay(env):
    e=env
    await invoke(e,'plan_retention')
    await toggle(e,'full_include_media',False)
    await toggle(e,'apply_unlocked')
    saved=e.hass.states.get('sensor.bma_backup_retention_plan').attributes
    path=e.hass.config.config_dir
    await e.hass.async_stop(force=True)
    restarted=HomeAssistant(path)
    restarted.config.skip_pip=True
    loader.async_setup(restarted)
    assert await bootstrap.async_from_config_dict(await package_config(restarted),restarted) is restarted
    await restarted.async_start()
    await restarted.async_block_till_done()
    try:
        assert restarted.states.get('input_boolean.bma_backup_full_include_media').state=='off'
        assert restarted.states.get('input_boolean.bma_backup_initialized').state=='on'
        assert restarted.states.get('input_boolean.bma_backup_apply_unlocked').state=='off'
        assert restarted.states.get('sensor.bma_backup_retention_plan').attributes==saved
        assert restarted.states.get('sensor.bma_backup_status').state=='idle'
        assert not any(k in ['create','apply_retention'] for k,d in e.calls)
    finally:
        await restarted.async_stop(force=True)

def test_namespace_frontend_and_no_legacy_path():
    p=load_package()
    defined=set()
    for domain in ['input_boolean','input_number','input_select','input_datetime','script']:
        for key in p[domain]:
            assert key.startswith('bma_backup_')
            defined.add(domain+'.'+key)
    for block in p['template']:
        for domain in ['sensor','binary_sensor']:
            for item in block.get(domain,[]):
                assert item['unique_id'].startswith('bma_backup_')
                defined.add(item['default_entity_id'])
    for a in p['automation']:
        assert a['id'].startswith('bma_backup_') and a['alias'].startswith('bma_backup_')
    text=(ROOT/'package/pkg_backup_home_assistant.yaml').read_text()
    for forbidden in ['shell_command:', 'command_line:', 'curl ', '/config/tmp/', 'last_known_slug', 'backup_remove.sh']:
        assert forbidden not in text
    import re
    ui=(ROOT/'package/ha_backup_frontend.yaml').read_text()
    yaml.safe_load(ui)
    for entity in re.findall(r'\b(?:script|sensor|binary_sensor|input_boolean|input_number|input_select|input_datetime)\.bma_backup_[a-z0-9_]+',ui):
        assert entity in defined, entity
    assert 'custom:' not in ui
    assert p['script']['bma_backup_worker']['trace']['stored_traces']==0


def test_notify_selector_survives_package_merge():
    old = {'selector': {'text': {}}}
    merged = {}
    _recursive_merge(merged, old)
    assert merged['selector'] == {}
    with pytest.raises(vol.Invalid, match='Only one type can be specified'):
        validate_selector(merged['selector'])
    field = load_package()['script']['bma_backup_notify']['fields']['message']
    merged = {}
    _recursive_merge(merged, field)
    selector = validate_selector(merged['selector'])
    assert set(selector) == {'text'}
    assert selector['text']['multiline'] is True


@pytest.mark.asyncio
async def test_notify_service_active_after_package_merge(env):
    assert env.hass.services.has_service('script', 'bma_backup_notify')
    await invoke(env, 'notify', message='Package merge notification test')
    assert any(n['message'] == 'Package merge notification test' for n in env.notices)


def test_frontend_card_and_dashboard_entry_points():
    card = yaml.safe_load((ROOT/'package/ha_backup_frontend.yaml').read_text())
    dashboard = yaml.safe_load((ROOT/'package/ha_backup_dashboard.yaml').read_text())
    assert card['type'] == 'vertical-stack'
    assert 'views' not in card
    assert dashboard['views'][0]['type'] == 'masonry'
    assert dashboard['views'][0]['cards'] == card['cards']
    def check_card(item):
        assert isinstance(item.get('type'), str) and item['type']
        for child in item.get('cards', []):
            check_card(child)
    check_card(card)


@pytest.mark.asyncio
@pytest.mark.parametrize('job', ['full', 'partial', 'ha_native', 'app_update'])
@pytest.mark.parametrize('destination,agent_id,domain', [
    ('network', 'hassio.Backup', 'hassio'),
    ('google_drive', 'google_drive.paolo_bertolli_gmail_com', 'google_drive'),
    ('s3', 's3_compatible.01M3HGM43E1SP3H02B0ZN5TRDC', 's3_compatible'),
])
async def test_external_destination_mapping(env, job, destination, agent_id, domain):
    """Exercise merged customizations and actual create/plan service scopes."""
    e = env
    e.state['agents'][agent_id] = {'name': destination, 'domain': domain}
    await toggle(e, 'destination_' + job + '_local', False)
    await toggle(e, 'destination_' + job + '_' + destination)
    selector = e.hass.states.get('input_boolean.bma_backup_destination_' + job + '_' + destination)
    assert selector.attributes['agent_id'] == agent_id
    if job in ['full', 'partial']:
        await invoke(e, 'run_' + job)
        creates = [data for service, data in e.calls if service == 'create']
        assert len(creates) == 1
        assert creates[0]['agent_ids'] == [agent_id]
    await e.hass.services.async_call('input_select', 'select_option', {
        'entity_id': 'input_select.bma_backup_retention_profile', 'option': job,
    }, blocking=True)
    await invoke(e, 'plan_retention')
    plans = [data for service, data in e.calls if service == 'plan_retention']
    assert len(plans) == 1
    assert plans[0]['agent_ids'] == [agent_id]
    assert plans[0]['source_type'] == ('bma' if job in ['full', 'partial'] else job)
    assert not any(service == 'apply_retention' for service, data in e.calls)
