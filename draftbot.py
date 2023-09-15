import discord
from discord.ext import commands
import asyncio

# Initialize the bot and set the command prefix
bot = commands.Bot(command_prefix='/')

# Dictionary to store player information (name, star rating, and position)
player_pool = {}

# Dictionary to store scouting attempts for each user
scout_attempts = {}

# Dictionary to store team names
team_names = {}

# Variables to control the draft
draft_in_progress = False
draft_channel = None
current_round = 1
current_pick = 1
total_teams = 10  # Default total number of teams
total_rounds = 5  # Default total number of rounds
draft_timer_minutes = 3  # Default draft timer duration in minutes

# Initialize a dictionary to track users with expired timers
expired_timers = {}

# Function to start the draft
async def start_draft():
    global draft_in_progress, current_round, current_pick
    draft_in_progress = True
    current_round = 1
    current_pick = 1
    while current_round <= total_rounds:
        team_on_clock = get_team_on_clock()
        await draft_channel.send(f"{team_on_clock} is on the clock.")
        await asyncio.sleep(draft_timer_minutes * 60)  # Sleep for draft timer duration
        
        # Check if the user's timer ran out
        if team_on_clock in expired_timers:
            await draft_channel.send(f"{team_on_clock}'s timer ran out.")
            
            # Provide options for auto-pick or manual selection
            await draft_channel.send(f"Options for {team_on_clock}:"
                                      "\n1. /auto-pick"
                                      "\n2. /select-player (playername)")
            
            # Listen for the user's choice
            def check_choice(msg):
                return msg.author == team_on_clock and msg.content.startswith(('/auto-pick', '/select-player'))
            
            try:
                choice_msg = await bot.wait_for('message', check=check_choice, timeout=60)
                if choice_msg.content.startswith('/auto-pick'):
                    selected_player = get_random_player()  # Replace with your logic
                elif choice_msg.content.startswith('/select-player'):
                    selected_player = choice_msg.content.split('/select-player ')[1]
            except asyncio.TimeoutError:
                selected_player = get_random_player()  # Auto-pick if no choice is made
            
            await draft_channel.send(f"{team_on_clock} has selected {selected_player} with the R{current_round} Pick #{current_pick}")
            current_pick += 1
            if current_pick > total_teams:
                current_pick = 1
                current_round += 1
            del expired_timers[team_on_clock]
        else:
            await draft_channel.send(f"{team_on_clock} has selected a player.")
            current_pick += 1
            if current_pick > total_teams:
                current_pick = 1
                current_round += 1

# Function to get the team currently on the clock
def get_team_on_clock():
    team_index = (current_pick - 1) % total_teams
    return team_names.get(team_index, f"Team {team_index + 1}")

# Replace this function with your logic to select players during the draft
def get_random_player():
    # Replace with your logic to select players from the player pool
    # For now, we'll return a placeholder name.
    return "Placeholder Player"

# Bot command to add a player to the player pool
@bot.command()
async def add_player(ctx, name, star_rating, position):
    player_pool[name] = {"star_rating": star_rating, "position": position}
    await ctx.send(f"Added {name} to the player pool.")

# Bot command to scout a player
@bot.command()
async def scout(ctx, name):
    user_id = ctx.author.id
    if user_id not in scout_attempts:
        scout_attempts[user_id] = 0

    if scout_attempts[user_id] < 3:
        if name in player_pool:
            await ctx.send(f"{name} - Star Rating: {player_pool[name]['star_rating']}")
            scout_attempts[user_id] += 1
        else:
            await ctx.send("Player not found in the pool.")
    else:
        await ctx.send("You have used all your scouting attempts.")

# Bot command to begin the draft
@bot.command()
async def draft_begin(ctx):
    global draft_channel
    draft_channel = discord.utils.get(ctx.guild.text_channels, name="draft")
    
    if draft_in_progress:
        await ctx.send("A draft is already in progress.")
    else:
        await ctx.send("Starting the draft.")
        await start_draft()

# Bot command to end the draft
@bot.command()
async def draft_end(ctx):
    global draft_in_progress
    if draft_in_progress:
        draft_in_progress = False
        await ctx.send("Ending the draft.")
    else:
        await ctx.send("No draft is currently in progress.")

# Bot command to set total_teams, total_rounds, and draft_timer_minutes
@bot.command()
async def set_settings(ctx, teams: int, rounds: int, timer_minutes: int):
    global total_teams, total_rounds, draft_timer_minutes
    total_teams = teams
    total_rounds = rounds
    draft_timer_minutes = timer_minutes
    await ctx.send("Settings updated.")

# Bot command to add or update team names
@bot.command()
async def set_team_name(ctx, team_number: int, *, name):
    team_names[team_number - 1] = name
    await ctx.send(f"Team {team_number} is now known as {name}.")

# Bot command to list team names
@bot.command()
async def list_team_names(ctx):
    team_list = "\n".join([f"Team {i + 1}: {name}" for i, name in team_names.items()])
    await ctx.send(f"Team Names:\n{team_list}")

# Bot command to allow users to set their timer as expired
@bot.command()
async def set_timer_expired(ctx):
    # Check if the user has the "mod" role
    if any(role.name == "mod" for role in ctx.author.roles):
        expired_team = get_team_on_clock()
        expired_timers[expired_team] = True
        await draft_channel.send(f"{expired_team}'s timer has been set as expired.")
    else:
        await ctx.send("You are not authorized to set timers as expired.")

# Run the bot with your token
bot.run("YOUR_DISCORD_BOT_TOKEN")
