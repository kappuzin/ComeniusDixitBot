# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 20:09:46 2020

@author: kornilov
"""
import os
import glob
import random
import tempfile
import pickle
import numpy
from matplotlib.image import imread
from matplotlib.image import imsave

import discord
from discord.ext import commands

class Player:
	def __init__(self, name, channel):
		self.name=name
		self.channel=channel
		self.score=0
		self.cards=[]

class Game:
	def __init__(self):
		# cards
		self.cards=[]
		# randomized stack of cards
		self.stack=[]
		# cards on the table
		self.play=[]
		# pool of players
		self.players=[]
		# current hand
		self.hand = 0
		# betting
		self.bet = []
		# game mode: 0 - no game, 1 - association, 2 - choosing cards, 3 - betting
		self.mode = 0
		# game owner, the one who started it
		self.owner = ''
		
	def in_game(self):
		str=''
		for pl in self.players:
			str = str + ' ' + pl.name
		return str
		
	def find_player(self,name):
		n=0
		for pl in self.players:
			if (pl.name==name):
				return n
			n=n+1
		return n
		
	def count_score_calc(self):
		flag=0
		for k in range(0,len(self.players)):
			if (k!=self.hand and self.play[self.bet[k]][0]==self.hand):
				flag=flag+1
		# everyone guessed?
		if (flag==len(self.players)-1):
			for k in range(0,len(self.players)):
				if (k!=self.hand):
					self.players[k].score=self.players[k].score+2
			return	
				
		flag=0
		for k in range(0,len(self.players)):
			if (k!=self.hand):
				if (self.play[self.bet[k]][0]==self.hand):		
					self.players[k].score=self.players[k].score+3
					flag=1
				else:
					self.players[self.play[self.bet[k]][0]].score=self.players[self.play[self.bet[k]][0]].score+1
				
		# no one guessed
		if (flag==0):
			for k in range(0,len(self.players)):
				if (k!=self.hand):
					self.players[k].score=self.players[k].score+2
		# someone guessed
		else:
			self.players[self.hand].score=self.players[self.hand].score+3
	
	def count_score(self):
		oldscore=[]
		for pl in self.players:
			oldscore.append(pl.score)
			
		self.count_score_calc()
	
		text='кто -> кого выбрал = сколько очков\n'
		for k in range(0,len(self.players)):
			deltascore=self.players[k].score-oldscore[k]
			text=text+self.players[k].name
			if (k!=self.hand):
				text=text+' -> '+self.players[self.play[self.bet[k]][0]].name
			else:
				text=text+' -> ------'
			text=text+' = +'+str(deltascore)+'\n'
			
		return text
	
	def status_text(self):
		text='начальница: '+self.owner+'\n'
		text=text+'игроки:'+self.in_game()+'\n'
		if (self.mode==0):
			text=text+'игра еще не началась\n'
		elif (self.mode==1):
			text=text+'ход: '+self.players[self.hand].name
		elif (self.mode==2):
			text=text+'игроки'
			for k in range(0,len(self.players)):
				flag=0
				for l in range(0,len(self.play)):
					if (k==self.play[l][0]):
						flag=1
				if (flag==0):
					text=text+' '+self.players[k].name
			text=text+' еще не положили карту\n'		
		elif (self.mode==3):
			text=text+'игроки'
			for k in range(0,len(self.players)):
				if (self.bet[k]==-1):
					text=text+' '+self.players[k].name
			text=text+' еще не сделали выбор\n'
		return text
	
	def save_score(self, fname):
		score={}
		for pl in self.players:
			score[pl.name]=pl.score
		pickle.dump(score,open('score_'+fname+'.pkl','wb'))
		print('saved score in '+fname)
		
	def load_score(self,fname):
		score=pickle.load(open('score_'+fname+'.pkl','rb'))
		for pl in self.players:
			if (pl.name in score.keys()):
				pl.score=score[pl.name]
		print('loaded score from '+fname)
	
	async def tell_all(self,text):
		for pl in self.players:
			await pl.channel.send(text)
			
	async def tell_all_but_hand(self,text):
		for k in range(0,len(self.players)):
			if (k!=self.hand):
				await self.players[k].channel.send(text)
	
	def score_text(self):
		text='общий счет:\n'
		for pl in self.players:
			text=text+pl.name+' '+str(pl.score)+'\n'
		return text
	
	async def show_player_cards(self,k):
		if (k<0 or k>=len(self.players)):
			return
		img=[]
		for cd in self.players[k].cards:
			img.append(imread(cd))
		yourcards=numpy.hstack(img)
		fname=tempfile.mktemp('.jpg')
		imsave(fname,yourcards)		
		await self.players[k].channel.send(file=discord.File(fname))
		os.remove(fname)
	
	async def show_cards(self):
		await self.tell_all('ваши карты:')
		for k in range(0,len(self.players)):
			await self.show_player_cards(k)
		
	async def show_play(self):
		img=[]
		yourcards=[]
		ROW=6
		for k in range(0,len(self.play)):
			img.append(imread(self.play[k][1]))
		for l in range(0,len(img)//ROW):
			yourcards.append(numpy.hstack(img[l*ROW:(l+1)*ROW]))
		if (len(img)%ROW!=0):
			lastrow=numpy.hstack(img[(len(img)//ROW)*ROW:])
			if (len(img)>ROW):
				lastrow=numpy.pad(lastrow,((0,0),(0,numpy.shape(yourcards[0])[1]-numpy.shape(lastrow)[1]),(0,0)))
			yourcards.append(lastrow)
		if (len(yourcards)>1):
			yc=numpy.vstack(yourcards)
		else:
			yc=yourcards[0]
		fname=tempfile.mktemp('.jpg')
		imsave(fname,yc)
		for pl in self.players:
			await pl.channel.send(file=discord.File(fname))
		os.remove(fname)
	
	async def show_play_named(self):
		text='порядок карт:'
		for k in range(0,len(self.play)):		
				text=text+' | '+str(k+1)+' - '+self.players[self.play[k][0]].name
		await self.tell_all(text)
		
	async def tell_to_play(self):
		await self.tell_all_but_hand('игрок '+self.players[self.hand].name+' пошла, выбирайте свою карту')
		
	async def tell_to_choose(self):
		await self.show_play()
		await self.tell_all_but_hand('догадайтесь, какую карту положила '+self.players[self.hand].name)	

#--------------------------------------------------------------------		
# create the instance of the game and of the bot
game=Game()
bot=commands.Bot(command_prefix='!')


#--------------------------------------------------------------------
@bot.event
async def on_ready():
	print(f'{bot.user.name} connected')
	
@bot.event
async def on_command_error(ctx, error):
	print(ctx.author.name+': command error')
	await ctx.author.create_dm()
	await ctx.author.dm_channel.send('нет такой команды')

# join the game
@bot.command(name='join', help=' - присоединиться к игре')
async def join(ctx):
	global game
	
	await ctx.author.create_dm()
	name=ctx.author.name
	
	n=game.find_player(name)
	if (n<len(game.players)):
		await ctx.author.dm_channel.send('вы уже присоединились к игре')
		return
	
	if (game.mode==0):
		await ctx.author.create_dm()
		game.players.append(Player(name,ctx.author.dm_channel))	
		await ctx.author.dm_channel.send('Добро пожаловать!')
		await game.tell_all('игрок '+name+' присоединилась к игре')
		await ctx.author.dm_channel.send('уже в игре:'+game.in_game())
		print(name, 'joined')
		
	elif (game.mode==1):
		await ctx.author.create_dm()
		game.players.append(Player(name,ctx.author.dm_channel))
		game.players[-1].cards=game.stack[0:6]
		del game.stack[0:6]
		game.players[-1].score=0
		await ctx.author.dm_channel.send('Добро пожаловать!')
		await game.tell_all('игрок '+name+' присоединилась к игре')
		await ctx.author.dm_channel.send('ваши карты:')
		await game.show_player_cards(len(game.players)-1)
		await ctx.author.dm_channel.send('уже в игре:'+game.in_game())
		await ctx.author.dm_channel.send('ход: '+game.players[game.hand].name)		
		print(name, 'joined')
	else:
		await ctx.author.dm_channel.send('подождите, пока закончится кон')

@bot.command(name='j', help=' - присоединиться к игре')
async def j(ctx):
		await join(ctx)
		
# start the game
@bot.command(name='start', help=' - начать игру')
async def start(ctx):
	global game
	print(ctx.author.name, 'starting the game')
	
	if (game.mode!=0):
		await ctx.author.create_dm()
		await ctx.author.dm_channel.send('игра уже началась')
		return

	game.owner=ctx.author.name
	if (len(game.players)==0 or game.find_player(game.owner)==len(game.players)):
		await ctx.author.create_dm()
		game.players.append(Player(game.owner,ctx.author.dm_channel))
		
	game.stack=random.sample(game.cards,len(game.cards))
	for pl in game.players:
		pl.cards=game.stack[0:6]
		del game.stack[0:6]
		pl.score=0
	game.hand=random.randint(0,len(game.players)-1)
	game.mode=1
	await game.tell_all('Игра началась!')
	await game.show_cards()
	await game.tell_all(game.status_text())
	print(ctx.author.name, 'started the game')
		
# clear the game
@bot.command(name='clear', help=' - очистить игру')
async def clear(ctx):
	global game
	
	if (ctx.author.name!=game.owner):
		return
	
	game.players=[]
	game.mode=0
	await ctx.author.create_dm()
	await ctx.author.dm_channel.send('игра очищена')
	print(ctx.author.name, 'cleared the game')
	
# status of the game
@bot.command(name='status', help=' - что происходит?')
async def status(ctx):
	global game
	await ctx.author.create_dm()
	await ctx.author.dm_channel.send(game.score_text())
	await ctx.author.dm_channel.send(game.status_text())

# send text to everyone via the bot
@bot.command(name='text', help=' - послать сообщение всем кто в игре')
async def text(ctx, str):
	global game
	await game.tell_all(ctx.author.name+': '+str)
	
@bot.command(name='t', help=' - послать сообщение всем кто в игре')
async def t(ctx, str):	
	await text(ctx, str)
	
@bot.command(name='s', help=' - что происходит?')
async def s(ctx):
	await status(ctx)
	
# save score
@bot.command(name='save', help=' - сохранить счет')
async def save(ctx, fname):
	global game
	if (ctx.author.name!=game.owner):
		return
	game.save_score(fname)
	
# load score
@bot.command(name='load', help=' - загрузить счет')
async def load(ctx, fname):
	global game
	if (ctx.author.name!=game.owner):
		return
	game.load_score(fname)
	
# quit the game
@bot.command(name='quit', help=' - выйти из игры')
async def quit(ctx):
	global game
	n=game.find_player(ctx.author.name)
	if (n<0 or n>=len(game.players)):
			return
	if (game.mode>1):
		await ctx.author.dm_channel.send('выйти можно только в конце кона')
		return
		
	del game.players[n]
	if (game.hand>n):
		game.hand=game.hand-1
	
	await ctx.author.dm_channel.send('вы покинули игру')
	await game.tell_all('игрок '+ctx.author.name+' вышла из игры')
	print(ctx.author.name+' quits')

@bot.command(name='kick', help=' - выйти игрока из игры')
async def kick(ctx, name):
	global game
	if (ctx.author.name!=game.owner):
		return
	n=game.find_player(name)
	if (n>=len(game.players)):
		await ctx.author.dm_channel.send('игрока с именем '+name+' в игре нет')
		return
	if (game.mode>1):	
		await ctx.author.dm_channel.send('игрока можно выпустить только в конце кона')
		return
	
	del game.players[n]
	if (game.hand>n):
		game.hand=game.hand-1
		
	await game.tell_all('игрок '+name+' вышла из игры')
	print(name+' was kicked out of the game by '+ctx.author.name)
			
@bot.command(name='mycards', help=' - показать мои карты')
async def mycards(ctx):
	global game
	n = game.find_player(ctx.author.name)
	if (n<len(game.players)):
		await ctx.author.dm_channel.send('ваши карты:')
		await game.show_player_cards(n)
		
# play card N
@bot.command(name='card', help=' - выбрать карту')
async def card(ctx, number: int):
	global game
	print(ctx.author.name+': card '+str(number))
	
	number=number-1
	
	n=game.find_player(ctx.author.name)
	
	if (game.mode==0):
		await ctx.author.dm_channel.send('игра еще не началась')
		
	elif (game.mode==1):
		if (n!=game.hand):
			await ctx.author.dm_channel.send('сейчас ходит '+game.players[game.hand].name)
			return
		if (number<0 or number>len(game.players[game.hand].cards)-1):
			await ctx.author.dm_channel.send('у вас нет такой карты')
			return
			
		game.play=[]
		game.play.append((game.hand,game.players[game.hand].cards.pop(number)))
		game.mode=2
		await game.players[game.hand].channel.send('не забудьте сказать другим игрокам вашу ассоциацию')
		await game.players[game.hand].channel.send('подождите, пока другие игроки выберут свою карту')
		await game.tell_to_play()
			
	elif (game.mode==2):
		for k in range(0,len(game.play)):
			if (game.play[k][0]==n):
				await ctx.author.dm_channel.send('вы уже положили карту')
				return		
		if (number<0 or number>len(game.players[n].cards)-1):
			await ctx.author.dm_channel.send('у вас нет такой карты')
			return
			
		game.play.append((n,game.players[n].cards.pop(number)))
		await ctx.author.dm_channel.send('вы положили карту '+str(number+1))
		
		if (len(game.play)==len(game.players)):
			random.shuffle(game.play)
			game.bet=[]
			for k in range(0,len(game.players)):
				if (k==game.hand):
					game.bet.append(0)
				else:
					game.bet.append(-1)
			game.mode=3
			await game.tell_to_choose()
			await game.players[game.hand].channel.send('подождите, пока игроки выберут, какая карта по их мнению ваша')
		
	elif (game.mode==3):
		if (n==game.hand):
			await ctx.author.dm_channel.send('вы и так знаете, какая карта ваша')
			return
		if (number<0 or number>len(game.play)):
			await ctx.author.dm_channel.send('нет такой карты')
			return
		if (game.play[number][0]==n):
			await ctx.author.dm_channel.send('свою карту выбирать нельзя')
			return
		
		game.bet[n]=number
		await ctx.author.dm_channel.send('вы выбрали карту '+str(number+1))
		
		if (not(-1 in game.bet)):
			print (game.bet)
			await game.show_play_named()
			await game.tell_all('-----------------------------------------')
			await game.tell_all(game.count_score())
			await game.tell_all('-----------------------------------------')
			await game.tell_all(game.score_text())
			for pl in game.players:
				if (len(game.stack)>0):
					pl.cards.append(game.stack.pop(0))
			game.hand=game.hand+1
			if (game.hand==len(game.players)):
				game.hand=0
			game.mode=1
			await game.show_cards()
			await game.tell_all(game.status_text())
	
@bot.command(name='c', help=' - выбрать карту')
async def c(ctx, number: int):
	await card(ctx, number)
		
#---------------------------------------------------------------------------------------	
random.seed()

#game.cards=glob.glob('72dpi/*jpg')
game.cards=glob.glob('Dixit4/*jpg')

print(str(len(game.cards))+' cards')

TOKEN='NjkyODg4NzAyOTcxODA1NzY2.Xn1GMw.EPjbxLudJUF-2o2xTM7lSsZl_ik'
bot.run(TOKEN)

# + номера карт в ответе
# режим watch
# + укороченные команды
# + разделить печать -----
# + сообщение всем через бота
# x имя при присоединении
# + ошибка при присоединении во время игры
# + ошибка после выхода - hand?
# + поправить статус - счет только тому кто просит
# + порядок карт улучшить текст
# + отклик что удалось положить карту или нет
# нужен мутекс
# сообщение тому кто последний
