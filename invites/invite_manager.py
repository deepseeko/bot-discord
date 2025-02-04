import yaml
import os
import random
from discord import Embed
from data.data import YOUR_SERVER_ID, update_backup, wallets, ID_casino
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('7YASBot')

INVITES_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/invites.yaml')

def load_invites():
    if os.path.exists(INVITES_FILE_PATH):
        with open(INVITES_FILE_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    else:
        return {}

def save_invites(invites):
    filtered_invites = {k: v for k, v in invites.items() if isinstance(v, dict) and 'invite_count' in v}
    with open(INVITES_FILE_PATH, 'w') as f:
        yaml.safe_dump(filtered_invites, f, default_flow_style=False)

async def handle_member_join(member, bot):
    if member.guild.id == YOUR_SERVER_ID:
        invites = await member.guild.invites()
        invite_uses = load_invites()

        for invite in invites:
            if invite.uses > invite_uses.get(invite.code, {}).get('uses', 0):
                inviter_id = str(invite.inviter.id)
                member_id = str(member.id)

                if inviter_id not in invite_uses:
                    invite_uses[inviter_id] = {
                        'username': invite.inviter.name,
                        'invites': {},
                        'invite_count': 0
                    }

                invite_uses[inviter_id]['invites'][member_id] = {
                    'username': member.name,
                    'invite_count': 0
                }
                invite_uses[inviter_id]['invite_count'] += 1

                if inviter_id in wallets and member_id not in wallets:
                    wallets[member_id] = {'balance': 0.0, 'username': member.name, 'last_daily': None}
                    bonus = random.randint(1, 10)
                    wallets[ID_casino]['balance'] -= bonus
                    wallets[inviter_id]['balance'] += bonus
                    await update_backup()

                    logger.info(f"Added {bonus} 7Y to {invite.inviter.name} for inviting {member.name}")

                    embed = Embed(
                        title="Invite Reward",
                        description=f"**`{bonus}` 7YAS coins added to your wallet for inviting `{member.name}`!**",
                        color=0x00ff00
                    )
                    embed.add_field(name="Total Invites", value=f"{invite_uses[inviter_id]['invite_count']} members.")
                    try:
                        await invite.inviter.send(embed=embed)
                    except Exception as e:
                        logger.error(f"Couldn't send message to inviter: {e}")

                save_invites(invite_uses)
                break
