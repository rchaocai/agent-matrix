"""
Agent管理API路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models import Agent
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone


router = APIRouter()


class AgentResponse(BaseModel):
    """Agent响应模型"""
    id: str
    name: str
    enabled: bool
    config: Optional[str] = None
    account_id: Optional[str] = None
    bound_account: Optional[dict] = None
    created_at: str
    updated_at: str
    today_published: int = 0
    daily_target: int = 3
    last_publish_time: str = "未运行"
    approval_rate: int = 0
    description: Optional[str] = None
    llm_provider: Optional[str] = None
    schedule: Optional[dict] = None


class AgentCreate(BaseModel):
    """创建Agent请求模型"""
    id: str
    name: str
    enabled: bool = True
    config: Optional[str] = None
    account_id: Optional[str] = None


class AgentUpdate(BaseModel):
    """更新Agent请求模型"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[str] = None
    account_id: Optional[str] = None


@router.get("/skills/list")
async def list_available_skills():
    """获取所有可用的Skill列表"""
    from app.main import agent_manager

    if not agent_manager or not agent_manager.skills_registry:
        return []

    skills = agent_manager.skills_registry.list_skills()

    # 按类别分组
    categories = {
        'generation': [],
        'review': [],
        'render': [],
        'publishing': [],
        'collection': [],
        'processing': [],
        'conditional': []
    }

    for skill in skills:
        name = skill['name']
        description = skill['description']

        # 分类
        if name.startswith('generation.'):
            if name == 'generation.render':
                categories['render'].append(skill)
            else:
                categories['generation'].append(skill)
        elif name.startswith('review.'):
            categories['review'].append(skill)
        elif name.startswith('publishing.'):
            categories['publishing'].append(skill)
        elif name.startswith('collection.'):
            categories['collection'].append(skill)
        elif name.startswith('processing.'):
            categories['processing'].append(skill)
        elif name.startswith('conditional.'):
            categories['conditional'].append(skill)

    # 转换为前端需要的格式
    result = []
    for category, skills_list in categories.items():
        if skills_list:
            result.append({
                'category': category,
                'label': {
                    'generation': '内容生成',
                    'review': '内容审核',
                    'render': '图文渲染',
                    'publishing': '内容发布',
                    'collection': '数据采集',
                    'processing': '数据处理',
                    'conditional': '条件控制'
                }.get(category, category),
                'skills': skills_list
            })

    return result


@router.get("/", response_model=List[AgentResponse])
async def list_agents():
    """获取所有Agent列表"""
    from pathlib import Path
    import yaml
    from app.models import Draft, Review, Account
    from datetime import datetime
    import json

    try:
        agents = await Agent.all()
        result = []

        # 获取所有账户（用于查找绑定账户信息）
        accounts = await Account.all()
        account_map = {acc.id: acc for acc in accounts}

        for agent in agents:
            try:
                # 计算今日发文数（使用北京时间计算今日）
                now_local = datetime.now()
                today_local = now_local.date()
                today_start_local = datetime.combine(today_local, datetime.min.time())
                today_start_utc = today_start_local - timedelta(hours=8)
                
                today_published = await Draft.filter(
                    agent_id=agent.id,
                    status='published',
                    created_at__gte=today_start_utc
                ).count()

                # 获取最后发文时间
                last_draft = await Draft.filter(
                    agent_id=agent.id,
                    status='published'
                ).order_by('-created_at').first()

                last_publish_time = "未运行"
                if last_draft and last_draft.created_at:
                    created_at = last_draft.created_at
                    
                    if created_at.tzinfo is not None:
                        created_at = created_at.replace(tzinfo=None)
                    
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    diff = (now - created_at).total_seconds()
                    
                    if diff < 0:
                        local_time = created_at + timedelta(hours=8)
                        last_publish_time = local_time.strftime("%m-%d %H:%M")
                    elif diff < 60:
                        last_publish_time = f"{int(diff)}秒前"
                    elif diff < 3600:
                        last_publish_time = f"{int(diff / 60)}分钟前"
                    elif diff < 86400:
                        last_publish_time = f"{int(diff / 3600)}小时前"
                    else:
                        local_time = created_at + timedelta(hours=8)
                        last_publish_time = local_time.strftime("%m-%d %H:%M")

                # 计算审核通过率
                total_reviews = await Review.filter(agent_id=agent.id).count()
                approved_reviews = await Review.filter(
                    agent_id=agent.id,
                    status='approved'
                ).count()

                approval_rate = 0
                if total_reviews > 0:
                    approval_rate = int((approved_reviews / total_reviews) * 100)

                # 获取绑定的账户信息
                bound_account = None
                if agent.account_id and agent.account_id in account_map:
                    acc = account_map[agent.account_id]
                    bound_account = {
                        'id': acc.id,
                        'name': acc.name,
                        'platform': acc.platform
                    }

                # 从 YAML 文件读取 agent 配置
                yaml_filename = f"{agent.id}.yaml" if agent.id.endswith('_agent') else f"{agent.id}_agent.yaml"
                yaml_path = Path(f"config/agents/{yaml_filename}")
                
                description = None
                llm_provider = None
                schedule = None
                
                if yaml_path.exists():
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            yaml_config = yaml.safe_load(f)
                            if yaml_config and 'agent' in yaml_config:
                                agent_config = yaml_config['agent']
                                description = agent_config.get('description')
                                llm_provider = agent_config.get('llm_provider')
                                schedule = agent_config.get('schedule')
                    except Exception as e:
                        print(f"Warning: Failed to load YAML for {agent.id}: {e}")

                result.append(
                    AgentResponse(
                        id=agent.id,
                        name=agent.name,
                        enabled=agent.enabled,
                        config=agent.config,
                        account_id=agent.account_id,
                        bound_account=bound_account,
                        created_at=agent.created_at.isoformat(),
                        updated_at=agent.updated_at.isoformat(),
                        today_published=today_published,
                        daily_target=3,
                        last_publish_time=last_publish_time,
                        approval_rate=approval_rate,
                        description=description,
                        llm_provider=llm_provider,
                        schedule=schedule
                    )
                )
            except Exception as e:
                print(f"Error processing agent {agent.id}: {e}")
                import traceback
                traceback.print_exc()
                continue

        return result
    except Exception as e:
        print(f"Error in list_agents: {e}")
        import traceback
        traceback.print_exc()
        return []


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """获取指定Agent详情"""
    from pathlib import Path
    import yaml
    from app.models import Account
    
    agent = await Agent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")
    
    # 获取绑定的账户信息
    bound_account = None
    if agent.account_id:
        account = await Account.get_or_none(id=agent.account_id)
        if account:
            bound_account = {
                'id': account.id,
                'name': account.name,
                'platform': account.platform
            }
    
    # 从 YAML 文件读取 agent 配置
    yaml_filename = f"{agent_id}.yaml" if agent_id.endswith('_agent') else f"{agent_id}_agent.yaml"
    yaml_path = Path(f"config/agents/{yaml_filename}")
    
    description = None
    llm_provider = None
    schedule = None
    
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config and 'agent' in yaml_config:
                    agent_config = yaml_config['agent']
                    description = agent_config.get('description')
                    llm_provider = agent_config.get('llm_provider')
                    schedule = agent_config.get('schedule')
        except Exception as e:
            print(f"Warning: Failed to load YAML for {agent_id}: {e}")
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        enabled=agent.enabled,
        config=agent.config,
        account_id=agent.account_id,
        bound_account=bound_account,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
        description=description,
        llm_provider=llm_provider,
        schedule=schedule
    )


@router.post("/{agent_id}/run")
async def trigger_agent(agent_id: str):
    """手动触发Agent执行"""
    from app.main import agent_manager

    # 检查Agent是否存在
    agent = await Agent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    if not agent.enabled:
        raise HTTPException(status_code=400, detail="Agent未启用")

    # 执行Agent（在后台运行）
    import asyncio
    asyncio.create_task(agent_manager.run_agent(agent_id))

    return {
        "message": f"Agent {agent_id} 开始执行",
        "status": "running",
        "agent_id": agent_id
    }


@router.get("/skills/list")
async def list_available_skills():
    """获取所有可用的Skill列表"""
    from app.main import agent_manager

    if not agent_manager or not agent_manager.skills_registry:
        return []

    skills = agent_manager.skills_registry.list_skills()

    # 按类别分组
    categories = {
        'generation': [],
        'review': [],
        'render': [],
        'publishing': [],
        'collection': [],
        'processing': [],
        'conditional': []
    }

    for skill in skills:
        name = skill['name']
        description = skill['description']

        # 分类
        if name.startswith('generation.'):
            if name == 'generation.render':
                categories['render'].append(skill)
            else:
                categories['generation'].append(skill)
        elif name.startswith('review.'):
            categories['review'].append(skill)
        elif name.startswith('publishing.'):
            categories['publishing'].append(skill)
        elif name.startswith('collection.'):
            categories['collection'].append(skill)
        elif name.startswith('processing.'):
            categories['processing'].append(skill)
        elif name.startswith('conditional.'):
            categories['conditional'].append(skill)

    # 转换为前端需要的格式
    result = []
    for category, skills_list in categories.items():
        if skills_list:
            result.append({
                'category': category,
                'label': {
                    'generation': '内容生成',
                    'review': '内容审核',
                    'render': '图文渲染',
                    'publishing': '内容发布',
                    'collection': '数据采集',
                    'processing': '数据处理',
                    'conditional': '条件控制'
                }.get(category, category),
                'skills': skills_list
            })

    return result


@router.post("/", response_model=AgentResponse)
async def create_agent(data: AgentCreate):
    """创建新Agent"""
    import yaml
    from pathlib import Path

    # 检查ID是否已存在
    existing = await Agent.get_or_none(id=data.id)
    if existing:
        raise HTTPException(status_code=400, detail="Agent ID已存在")

    agent = await Agent.create(
        id=data.id,
        name=data.name,
        enabled=data.enabled,
        config=data.config,
        account_id=data.account_id
    )

    # 创建YAML配置文件
    yaml_filename = f"{data.id}.yaml" if data.id.endswith('_agent') else f"{data.id}_agent.yaml"
    yaml_path = Path(f"config/agents/{yaml_filename}")
    
    if data.config:
        try:
            config_dict = yaml.safe_load(data.config)
            if config_dict:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(config_dict, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Warning: Failed to create YAML file: {e}")
    else:
        # 创建默认配置
        default_config = {
            'agent': {
                'id': data.id,
                'name': data.name,
                'description': f'{data.name} Agent',
                'enabled': data.enabled,
                'llm_provider': 'deepseek',
                'skill_chain': []
            }
        }
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(default_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # 加载Agent到内存
    from app.main import agent_manager
    if agent_manager and data.enabled:
        try:
            await agent_manager.load_agent(yaml_path)
        except Exception as e:
            print(f"Warning: Failed to load agent: {e}")

    # 从 YAML 文件读取 agent 配置
    description = None
    llm_provider = None
    schedule = None
    
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config and 'agent' in yaml_config:
                    agent_config = yaml_config['agent']
                    description = agent_config.get('description')
                    llm_provider = agent_config.get('llm_provider')
                    schedule = agent_config.get('schedule')
        except Exception as e:
            print(f"Warning: Failed to load YAML for {data.id}: {e}")

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        enabled=agent.enabled,
        config=agent.config,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
        description=description,
        llm_provider=llm_provider,
        schedule=schedule
    )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, data: AgentUpdate):
    """更新Agent"""
    import yaml
    from pathlib import Path

    agent = await Agent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    # 更新数据库字段
    if data.name is not None:
        agent.name = data.name
    if data.enabled is not None:
        agent.enabled = data.enabled
    if data.config is not None:
        agent.config = data.config
    if data.account_id is not None:
        agent.account_id = data.account_id

    await agent.save()

    # 同步更新YAML配置文件
    yaml_filename = f"{agent_id}.yaml" if agent_id.endswith('_agent') else f"{agent_id}_agent.yaml"
    yaml_path = Path(f"config/agents/{yaml_filename}")
    if data.config is not None:
        try:
            config_dict = yaml.safe_load(data.config)
            if config_dict:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(config_dict, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Warning: Failed to update YAML file: {e}")
            import traceback
            traceback.print_exc()

    # 重新加载Agent
    from app.main import agent_manager
    if agent_manager:
        try:
            await agent_manager.reload_agent(agent_id)
            print(f"Agent {agent_id} 已重新加载")
        except Exception as e:
            print(f"Warning: Failed to reload agent: {e}")

    # 从 YAML 文件读取 agent 配置
    description = None
    llm_provider = None
    schedule = None
    
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config and 'agent' in yaml_config:
                    agent_config = yaml_config['agent']
                    description = agent_config.get('description')
                    llm_provider = agent_config.get('llm_provider')
                    schedule = agent_config.get('schedule')
        except Exception as e:
            print(f"Warning: Failed to load YAML for {agent_id}: {e}")

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        enabled=agent.enabled,
        config=agent.config,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
        description=description,
        llm_provider=llm_provider,
        schedule=schedule
    )


@router.patch("/{agent_id}/toggle")
async def toggle_agent(agent_id: str):
    """切换Agent启用状态"""
    import yaml
    from pathlib import Path
    
    agent = await Agent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    agent.enabled = not agent.enabled
    await agent.save()
    
    # 同步更新YAML配置文件
    yaml_filename = f"{agent_id}.yaml" if agent_id.endswith('_agent') else f"{agent_id}_agent.yaml"
    yaml_path = Path(f"config/agents/{yaml_filename}")
    
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
            
            if yaml_config and 'agent' in yaml_config:
                yaml_config['agent']['enabled'] = agent.enabled
                
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(yaml_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                
                print(f"✓ 已更新YAML配置文件: {yaml_filename}, enabled={agent.enabled}")
        except Exception as e:
            print(f"Warning: Failed to update YAML file: {e}")
            import traceback
            traceback.print_exc()
    
    # 重新加载Agent
    from app.main import agent_manager
    if agent_manager:
        try:
            if agent.enabled:
                # 如果启用，重新加载Agent
                await agent_manager.reload_agent(agent_id)
                print(f"✓ Agent {agent_id} 已重新加载并启用")
            else:
                # 如果禁用，停止Agent
                await agent_manager.stop_agent(agent_id)
                print(f"✓ Agent {agent_id} 已停止")
        except Exception as e:
            print(f"Warning: Failed to reload agent: {e}")

    return {
        "message": f"Agent {agent_id} 已{'启用' if agent.enabled else '禁用'}",
        "enabled": agent.enabled
    }


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """删除Agent"""
    from pathlib import Path

    agent = await Agent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")
    
    # 从内存中移除
    from app.main import agent_manager
    if agent_manager:
        await agent_manager.stop_agent(agent_id)
    
    # 删除YAML文件
    yaml_filename = f"{agent_id}.yaml" if agent_id.endswith('_agent') else f"{agent_id}_agent.yaml"
    yaml_path = Path(f"config/agents/{yaml_filename}")
    if yaml_path.exists():
        yaml_path.unlink()
    
    await agent.delete()
    return {"message": f"Agent {agent_id} 已删除"}
