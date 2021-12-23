# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import subprocess
import threading
import sys
import os

###########################################################################
## Class MyFrame
###########################################################################

class MyFrame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self,parent,id = -1,title='',pos = wx.Point(1,1),size = wx.Size(740,740),style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX,name = 'frame' )
		
		self.SetTitle('NFTool Gui by flix88')
		self.Show(False)

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		
		#codec
		self.chc54c = wx.Choice(self,-1,wx.Point(10,30),wx.Size(120,41),[r'H264',r'HEVC',r'HDR'])
		self.chc54c.SetFont(wx.Font(12,74,90,90,0,"Tahoma"))
		
		#reslution
		self.chc64c = wx.Choice(self,-1,wx.Point(150,30),wx.Size(120,41),[r'SD',r'720p',r'1080p'])
		self.chc64c.SetFont(wx.Font(12,74,90,90,0,"Tahoma"))
		
		
		#series
		
		self.chc74c = wx.Choice(self,-1,wx.Point(290,30),wx.Size(120,41),[r'1',r'2',r'3',r'4',r'5',r'6',r'7',r'8',r'9',r'10',r'11',r'12',r'13',r'14',r'15',r'16',r'17',r'18',r'19',r'20'])
		self.chc74c.SetFont(wx.Font(12,74,90,90,0,"Tahoma"))
		
		
		#episode
		
		self.chc84c = wx.Choice(self,-1,wx.Point(420,30),wx.Size(120,41),[r'1',r'2',r'3',r'4',r'5',r'6',r'7',r'8',r'9',r'10',r'11',r'12',r'13',r'14',r'15',r'16',r'17',r'18',r'19',r'20'])
		self.chc84c.SetFont(wx.Font(12,74,90,90,0,"Tahoma"))
		
		
		#audio
		self.lc7c = wx.CheckListBox(self,-1,wx.Point(550,30),wx.Size(120,120),[r'de',r'en',r'es-ES',r'es',r'fr',r'it',r'ja',r'pl',r'pt-BR',r'ru',r'tr',r'nl-BE',r'nb',r'fi',r'cs',r'zh',r'yue',r'ko',r'ar',r'he',r'zxx'])
		
		
		self.st64c = wx.StaticText(self,-1,"",wx.Point(50,10),wx.Size(104,20),wx.ST_NO_AUTORESIZE)
		self.st64c.SetLabel("Codec")
		self.st64c.SetFont(wx.Font(9,74,90,90,0,"Tahoma"))
		
		
		self.st74c = wx.StaticText(self,-1,"",wx.Point(180,10),wx.Size(104,20),wx.ST_NO_AUTORESIZE)
		self.st74c.SetLabel("Resolution")
		self.st74c.SetFont(wx.Font(9,74,90,90,0,"Tahoma"))
		
		
		self.st84c = wx.StaticText(self,-1,"",wx.Point(330,10),wx.Size(104,20),wx.ST_NO_AUTORESIZE)
		self.st84c.SetLabel("Series")
		self.st84c.SetFont(wx.Font(9,74,90,90,0,"Tahoma"))
		
		
		self.st94c = wx.StaticText(self,-1,"",wx.Point(455,10),wx.Size(104,20),wx.ST_NO_AUTORESIZE)
		self.st94c.SetLabel("Episode")
		self.st94c.SetFont(wx.Font(9,74,90,90,0,"Tahoma"))
		
		
		self.st54c = wx.StaticText(self,-1,"",wx.Point(590,10),wx.Size(104,20),wx.ST_NO_AUTORESIZE)
		self.st54c.SetLabel("Audio")
		self.st54c.SetFont(wx.Font(9,74,90,90,0,"Tahoma"))
		
		
		self.st44c = wx.StaticText(self,-1,"",wx.Point(50,65),wx.Size(104,15),wx.ST_NO_AUTORESIZE)
		self.st44c.SetLabel("Url")
		self.st44c.SetFont(wx.Font(9,74,90,90,0,"Tahoma"))
		

		self.txm17c = wx.TextCtrl(self,-1,"",wx.Point(10,85),wx.Size(320,55),wx.TE_MULTILINE)
		self.txm17c.SetFont(wx.Font(11,74,90,90,0,"Tahoma"))
		
		self.txm23c = wx.TextCtrl(self,-1,"",wx.Point(10,155),wx.Size(660,450),wx.FULL_REPAINT_ON_RESIZE|wx.VSCROLL|wx.HSCROLL|wx.TE_MULTILINE)
		self.txm23c.SetFont(wx.Font(10,74,90,90,0,"Tahoma"))
		
		
			
		
		self.bt55c = wx.Button(self,-1,"",wx.Point(10,620),wx.Size(150,60))
		self.bt55c.SetLabel("Download")
		self.bt55c.SetFont(wx.Font(12,74,90,90,0,"Tahoma"))
		self.Bind(wx.EVT_BUTTON,self.bt55c_VwXEvOnButtonClick,self.bt55c)
		
		self.bt65c = wx.Button(self,-1,"",wx.Point(180,620),wx.Size(150,60))
		self.bt65c.SetLabel("Playlist")
		self.bt65c.SetFont(wx.Font(12,74,90,90,0,"Tahoma"))
		self.Bind(wx.EVT_BUTTON,self.bt65c_VwXEvOnButtonClick,self.bt65c)
		
		
		self.ck66c = wx.CheckBox(self,-1,"",wx.Point(470,80),wx.Size(18,21))
		self.st66c = wx.StaticText(self,-1,"",wx.Point(460,60),wx.Size(90,22),wx.ST_NO_AUTORESIZE)
		self.st66c.SetLabel("Debug")
		

		#self.SetSizer( bSizer2 )
		self.Layout()

		self.Centre( wx.BOTH )
		

	def __del__( self ):
		pass
		
		
	def get_playlist(self, event):
		
		if self.chc54c.GetSelection() == 0:
			#self.txm23c.SetValue('h264')
			codec = 'h264'
		if self.chc54c.GetSelection() == 1:
			#self.txm23c.SetValue('hevc')
			codec = 'hevc'
		if self.chc54c.GetSelection() == 2:
			#self.txm23c.SetValue('hdr')
			codec = 'hdr'
		
		if self.chc64c.GetSelection() == 0:
			#self.txm23c.SetValue('sd')
			res = 'sd'
		if self.chc64c.GetSelection() == 1:
			#self.txm23c.SetValue('720p')
			res = '720p'
		if self.chc64c.GetSelection() == 2:
			#self.txm23c.SetValue('1080p')
			res = '1080p'	
		
		if self.chc74c.GetSelection() == 0:
			#self.txm23c.SetValue('1')
			series = '1'
		if self.chc74c.GetSelection() == 1:
			#self.txm23c.SetValue('2')
			series = '2'
		if self.chc74c.GetSelection() == 2:
			#self.txm23c.SetValue('3')
			series = '3'
		if self.chc74c.GetSelection() == 3:
			#self.txm23c.SetValue('4')
			series = '4'
		if self.chc74c.GetSelection() == 4:
			#self.txm23c.SetValue('5')
			series = '5'
		if self.chc74c.GetSelection() == 5:
			#self.txm23c.SetValue('6')
			series = '6'
		if self.chc74c.GetSelection() == 6:
			#self.txm23c.SetValue('7')
			series = '7'
		if self.chc74c.GetSelection() == 7:
			#self.txm23c.SetValue('8')
			series = '8'
		if self.chc74c.GetSelection() == 8:
			#self.txm23c.SetValue('9')
			series = '9'
		if self.chc74c.GetSelection() == 9:
			#self.txm23c.SetValue('10')
			series = '10'
		if self.chc74c.GetSelection() == 10:
			#self.txm23c.SetValue('11')
			series = '11'
		if self.chc74c.GetSelection() == 11:
			#self.txm23c.SetValue('12')
			series = '12'
		if self.chc74c.GetSelection() == 12:
			#self.txm23c.SetValue('13')
			series = '13'
		if self.chc74c.GetSelection() == 13:
			#self.txm23c.SetValue('14')
			series = '14'
		if self.chc74c.GetSelection() == 14:
			#self.txm23c.SetValue('15')
			series = '15'
		if self.chc74c.GetSelection() == 15:
			#self.txm23c.SetValue('16')
			series = '16'
		if self.chc74c.GetSelection() == 16:
			#self.txm23c.SetValue('17')
			series = '17'
		if self.chc74c.GetSelection() == 17:
			#self.txm23c.SetValue('18')
			series = '18'
		if self.chc74c.GetSelection() == 18:
			#self.txm23c.SetValue('19')
			series = '19'
		if self.chc74c.GetSelection() == 19:
			#self.txm23c.SetValue('20')
			series = '20'
			
			
		if self.chc84c.GetSelection() == 0:
			#self.txm23c.SetValue('1')
			episode = '1'
		if self.chc84c.GetSelection() == 1:
			#self.txm23c.SetValue('2')
			episode = '2'
		if self.chc84c.GetSelection() == 2:
			#self.txm23c.SetValue('3')
			episode = '3'
		if self.chc84c.GetSelection() == 3:
			#self.txm23c.SetValue('4')
			episode = '4'
		if self.chc84c.GetSelection() == 4:
			#self.txm23c.SetValue('5')
			episode = '5'
		if self.chc84c.GetSelection() == 5:
			#self.txm23c.SetValue('6')
			episode = '6'
		if self.chc84c.GetSelection() == 6:
			#self.txm23c.SetValue('7')
			episode = '7'
		if self.chc84c.GetSelection() == 7:
			#self.txm23c.SetValue('8')
			episode = '8'
		if self.chc84c.GetSelection() == 8:
			#self.txm23c.SetValue('9')
			episode = '9'
		if self.chc84c.GetSelection() == 9:
			#self.txm23c.SetValue('10')
			episode = '10'
		if self.chc84c.GetSelection() == 10:
			#self.txm23c.SetValue('11')
			episode = '11'
		if self.chc84c.GetSelection() == 11:
			#self.txm23c.SetValue('12')
			episode = '12'
		if self.chc84c.GetSelection() == 12:
			#self.txm23c.SetValue('13')
			episode = '13'
		if self.chc84c.GetSelection() == 13:
			#self.txm23c.SetValue('14')
			episode = '14'
		if self.chc84c.GetSelection() == 14:
			#self.txm23c.SetValue('15')
			episode = '15'
		if self.chc84c.GetSelection() == 15:
			#self.txm23c.SetValue('16')
			episode = '16'
		if self.chc84c.GetSelection() == 16:
			#self.txm23c.SetValue('17')
			episode = '17'
		if self.chc84c.GetSelection() == 17:
			#self.txm23c.SetValue('18')
			episode = '18'
		if self.chc84c.GetSelection() == 18:
			#self.txm23c.SetValue('19')
			episode = '19'
		if self.chc84c.GetSelection() == 19:
			#self.txm23c.SetValue('20')
			episode = '20'
		
		audio = []
		#self.txm23c.SetValue(str(self.lc7c.GetCheckedItems()))
		if self.lc7c.IsChecked(0):
			audio.append('de')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(1):
			audio.append('en')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(2):
			audio.append('es-ES')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(3):
			audio.append('es')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(4):
			audio.append('fr')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(5):
			audio.append('it')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(6):
			audio.append('ja')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(7):
			audio.append('pl')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(8):
			audio.append('pt-BR')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(9):
			audio.append('ru')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(10):
			audio.append('tr')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(11):
			audio.append('nl-BE')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(12):
			audio.append('nb')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(13):
			audio.append('fi')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(14):
			audio.append('cs')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(15):
			audio.append('zh')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(16):
			audio.append('yue')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(17):
			audio.append('ko')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(18):
			audio.append('ar')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(19):
			audio.append('he')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(20):
			audio.append('zxx')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		#cmd = "python netflix.py -t 80149092 -q sd -p h264 -a de"
		cmd = "python netflix.py -i"
		if self.ck66c.IsChecked():
			cmd1 = " -d"
		else:
			cmd1 = ""
		#https://www.netflix.com/de/title/80200571
		title =  self.txm17c.GetValue()
		
		cmd0 = title.split('title/')
		cmd0 = " -t " + cmd0[1]
		cmd2 = " -p " + codec
		cmd3 = " -q " + res
		cmd4 = " -a " + ','.join(audio)
		
		se = self.chc74c.GetSelection()
		ep = self.chc84c.GetSelection()
		
		if  se == -1 and ep == -1:
			cmd5 = ""
		
		if  se >= 0 and ep == -1:
			cmd5 = " -s " + series
			
		if  se >= 0 and ep >= 0:
			cmd5 = " -s " + series + " -e " + episode
				
		cmdd = cmd + cmd0 + cmd2 + cmd3 + cmd1 + cmd4 + cmd5
		print(cmdd)
		
		popenobj = subprocess.Popen(cmdd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		while not popenobj.poll():
			stdoutdata = popenobj.stdout.readline()
			if stdoutdata:
				#sys.stdout.write(stdoutdata.decode('cp1252'))
				wx.CallAfter(self.txm23c.AppendText, stdoutdata.decode('cp1252').encode('utf-8'))
			else:
				break
		print("Return code", popenobj.returncode)
	
	
	
	def get_download(self, event):
		
		if self.chc54c.GetSelection() == 0:
			#self.txm23c.SetValue('h264')
			codec = 'h264'
		if self.chc54c.GetSelection() == 1:
			#self.txm23c.SetValue('hevc')
			codec = 'hevc'
		if self.chc54c.GetSelection() == 2:
			#self.txm23c.SetValue('hdr')
			codec = 'hdr'
		
		if self.chc64c.GetSelection() == 0:
			#self.txm23c.SetValue('sd')
			res = 'sd'
		if self.chc64c.GetSelection() == 1:
			#self.txm23c.SetValue('720p')
			res = '720p'
		if self.chc64c.GetSelection() == 2:
			#self.txm23c.SetValue('1080p')
			res = '1080p'	
		
		if self.chc74c.GetSelection() == 0:
			#self.txm23c.SetValue('1')
			series = '1'
		if self.chc74c.GetSelection() == 1:
			#self.txm23c.SetValue('2')
			series = '2'
		if self.chc74c.GetSelection() == 2:
			#self.txm23c.SetValue('3')
			series = '3'
		if self.chc74c.GetSelection() == 3:
			#self.txm23c.SetValue('4')
			series = '4'
		if self.chc74c.GetSelection() == 4:
			#self.txm23c.SetValue('5')
			series = '5'
		if self.chc74c.GetSelection() == 5:
			#self.txm23c.SetValue('6')
			series = '6'
		if self.chc74c.GetSelection() == 6:
			#self.txm23c.SetValue('7')
			series = '7'
		if self.chc74c.GetSelection() == 7:
			#self.txm23c.SetValue('8')
			series = '8'
		if self.chc74c.GetSelection() == 8:
			#self.txm23c.SetValue('9')
			series = '9'
		if self.chc74c.GetSelection() == 9:
			#self.txm23c.SetValue('10')
			series = '10'
		if self.chc74c.GetSelection() == 10:
			#self.txm23c.SetValue('11')
			series = '11'
		if self.chc74c.GetSelection() == 11:
			#self.txm23c.SetValue('12')
			series = '12'
		if self.chc74c.GetSelection() == 12:
			#self.txm23c.SetValue('13')
			series = '13'
		if self.chc74c.GetSelection() == 13:
			#self.txm23c.SetValue('14')
			series = '14'
		if self.chc74c.GetSelection() == 14:
			#self.txm23c.SetValue('15')
			series = '15'
		if self.chc74c.GetSelection() == 15:
			#self.txm23c.SetValue('16')
			series = '16'
		if self.chc74c.GetSelection() == 16:
			#self.txm23c.SetValue('17')
			series = '17'
		if self.chc74c.GetSelection() == 17:
			#self.txm23c.SetValue('18')
			series = '18'
		if self.chc74c.GetSelection() == 18:
			#self.txm23c.SetValue('19')
			series = '19'
		if self.chc74c.GetSelection() == 19:
			#self.txm23c.SetValue('20')
			series = '20'
			
			
		if self.chc84c.GetSelection() == 0:
			#self.txm23c.SetValue('1')
			episode = '1'
		if self.chc84c.GetSelection() == 1:
			#self.txm23c.SetValue('2')
			episode = '2'
		if self.chc84c.GetSelection() == 2:
			#self.txm23c.SetValue('3')
			episode = '3'
		if self.chc84c.GetSelection() == 3:
			#self.txm23c.SetValue('4')
			episode = '4'
		if self.chc84c.GetSelection() == 4:
			#self.txm23c.SetValue('5')
			episode = '5'
		if self.chc84c.GetSelection() == 5:
			#self.txm23c.SetValue('6')
			episode = '6'
		if self.chc84c.GetSelection() == 6:
			#self.txm23c.SetValue('7')
			episode = '7'
		if self.chc84c.GetSelection() == 7:
			#self.txm23c.SetValue('8')
			episode = '8'
		if self.chc84c.GetSelection() == 8:
			#self.txm23c.SetValue('9')
			episode = '9'
		if self.chc84c.GetSelection() == 9:
			#self.txm23c.SetValue('10')
			episode = '10'
		if self.chc84c.GetSelection() == 10:
			#self.txm23c.SetValue('11')
			episode = '11'
		if self.chc84c.GetSelection() == 11:
			#self.txm23c.SetValue('12')
			episode = '12'
		if self.chc84c.GetSelection() == 12:
			#self.txm23c.SetValue('13')
			episode = '13'
		if self.chc84c.GetSelection() == 13:
			#self.txm23c.SetValue('14')
			episode = '14'
		if self.chc84c.GetSelection() == 14:
			#self.txm23c.SetValue('15')
			episode = '15'
		if self.chc84c.GetSelection() == 15:
			#self.txm23c.SetValue('16')
			episode = '16'
		if self.chc84c.GetSelection() == 16:
			#self.txm23c.SetValue('17')
			episode = '17'
		if self.chc84c.GetSelection() == 17:
			#self.txm23c.SetValue('18')
			episode = '18'
		if self.chc84c.GetSelection() == 18:
			#self.txm23c.SetValue('19')
			episode = '19'
		if self.chc84c.GetSelection() == 19:
			#self.txm23c.SetValue('20')
			episode = '20'
		
		audio = []
		#self.txm23c.SetValue(str(self.lc7c.GetCheckedItems()))
		if self.lc7c.IsChecked(0):
			audio.append('de')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(1):
			audio.append('en')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(2):
			audio.append('es-ES')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(3):
			audio.append('es')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(4):
			audio.append('fr')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(5):
			audio.append('it')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(6):
			audio.append('ja')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(7):
			audio.append('pl')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(8):
			audio.append('pt-BR')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(9):
			audio.append('ru')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(10):
			audio.append('tr')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(11):
			audio.append('nl-BE')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(12):
			audio.append('nb')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(13):
			audio.append('fi')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(14):
			audio.append('cs')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(15):
			audio.append('zh')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(16):
			audio.append('yue')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(17):
			audio.append('ko')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(18):
			audio.append('ar')
			#self.txm23c.SetValue(str(audio))
			print(audio)
		
		if self.lc7c.IsChecked(19):
			audio.append('he')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		if self.lc7c.IsChecked(20):
			audio.append('zxx')
			#self.txm23c.SetValue(str(audio))
			print(audio)
			
		#cmd = "python netflix.py -t 80149092 -q sd -p h264 -a de"
		cmd = "python netflix.py"
		if self.ck66c.IsChecked():
			cmd1 = " -d"
		else:
			cmd1 = ""
		#https://www.netflix.com/de/title/80200571
		title =  self.txm17c.GetValue()
		
		cmd0 = title.split('title/')
		cmd0 = " -t " + cmd0[1]
		cmd2 = " -p " + codec
		cmd3 = " -q " + res
		cmd4 = " -a " + ','.join(audio)
		
		se = self.chc74c.GetSelection()
		ep = self.chc84c.GetSelection()
		
		if  se == -1 and ep == -1:
			cmd5 = ""
		
		if  se >= 0 and ep == -1:
			cmd5 = " -s " + series
			
		if  se >= 0 and ep >= 0:
			cmd5 = " -s " + series + " -e " + episode
				
		cmdd = cmd + cmd0 + cmd2 + cmd3 + cmd1 + cmd4 + cmd5
		print(cmdd)
		
		popenobj = subprocess.Popen(cmdd, stdout=subprocess.PIPE)
		while not popenobj.poll():
			stdoutdata = popenobj.stdout.readline()
			if stdoutdata:
				#sys.stdout.write(stdoutdata.decode('cp1252'))
				wx.CallAfter(self.txm23c.AppendText, stdoutdata.decode('cp1252').encode('utf-8'))
			else:
				break
		print("Return code", popenobj.returncode)
	
	
	def bt65c_VwXEvOnButtonClick(self,event):
		
		th = threading.Thread(target=self.get_playlist, args=(event,))
		th.start()
		return
		
	def bt55c_VwXEvOnButtonClick(self,event):
		
		th = threading.Thread(target=self.get_download, args=(event,))
		th.start()
		return