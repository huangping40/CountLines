#!/usr/bin/env python
#
# Usage:
#
# python predict.py -r recordfile.txt  -i installment.txt  -y 1
#
# Version:	1.0
# Author:	norbert
# Date:		2017-10-19
#

import argparse
import re
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta

# 未来收入
class FutureRecord:
	cid = 0
	code = ""
	name = ""
	income = 0
	price = 0.0
	members =0
	startTime = datetime.strptime("2017-01-02", "%Y-%m-%d")
	endTime = datetime.strptime("2017-01-02", "%Y-%m-%d")

	def __init__(self, record):
		self.cid = record.cid
		self.code = record.code
		self.name = record.name

	def __repr__(self):
		return "{},{},{},{},{},{},{},{}".format(self.cid, self.code,
												self.name, self.income,
												self.price, self.members,
												self.startTime.strftime('%Y-%m-%d'),
												self.endTime.strftime('%Y-%m-%d'))

# 已经发生的收入
class Record:
	cid = 0
	code = ""
	name = ""
	income = 23
	startTime = datetime.strptime("2017-01-02", "%Y-%m-%d")
	endTime = datetime.strptime("2017-01-02", "%Y-%m-%d")
	members = 0
	periods = 0
	fixedPeriod = 0 # 已经缴纳的分期数
	currentPeriod = 0

	def __init__(self, arr):
		self.cid = int(arr[1])
		self.code = arr[2]
		self.name = arr[3]
		self.income = float(arr[4])
		self.startTime = datetime.strptime(arr[5], "%Y-%m-%d")
		self.endTime = datetime.strptime(arr[6], "%Y-%m-%d")
		self.members = int(arr[7])

	def merge(self, arr):
		# TODO: 连续订单情况还没有考虑
		self.income += float(arr[4])
		if self.endTime != datetime.strptime(arr[6], "%Y-%m-%d"):
			print("非法数据：同一个公司截至时间不一样：", arr)
			exit()
		self.members += int(arr[7])

	def predict(self, theDay):
	#	print(theDay,self.endTime)
		if self.periods == 0 and theDay <= self.endTime:
			return  None

		# 没有分期的情况或者分期满
		if (self.periods == 0 and theDay > self.endTime) or (self.periods > 0 and self.periods == self.currentPeriod):
			futureRecord = FutureRecord(self)
			futureRecord.price = 360
			futureRecord.members = self.members
			futureRecord.income = futureRecord.price * self.members
			futureRecord.startTime = theDay
			futureRecord.endTime = theDay + relativedelta(years=1) + timedelta(days=-1)

			self.endTime = futureRecord.endTime
			return  futureRecord

		days = int((self.endTime - self.startTime).days * self.currentPeriod / self.periods)
		predictDay = self.startTime +  timedelta(days=days)
		#print(" haha ", (self.endTime - self.startTime).days, ", self.fixedPeriod: " , self.fixedPeriod )
		#print("predictDay >= now:", predictDay, ", ",  theDay, ", days: " , days )
		if predictDay >= theDay:
			return None

		#分期没有满情况
		self.currentPeriod += 1
		days = int((self.endTime - self.startTime).days * self.currentPeriod / self.periods)
		predictDay = self.startTime + timedelta(days=days)

		futureRecord = FutureRecord(self)
		futureRecord.price = self.income / self.fixedPeriod / self.members
		futureRecord.members = self.members
		futureRecord.income = futureRecord.price * self.members
		futureRecord.startTime = theDay

		if self.periods == self.currentPeriod:
			futureRecord.endTime = self.endTime
		else:
			futureRecord.endTime = predictDay

		return futureRecord

	def mergeExtra(self, extra):
		if self.endTime != extra.endTime:
			print("原始订单和分期订单截至时间不一样：", str(self.__dict__), str(extra.__dict__))
			exit()
		if self.startTime != extra.startTime:
			print("原始订单和分期订单开始时间不一样：", str(self.__dict__), str(extra.__dict__))
			exit()
		if self.income != extra.income:
			print("原始订单和分期订单金额不一样：", str(self.__dict__), str(extra.__dict__))
			exit()

		self.periods = extra.periods
		self.currentPeriod = extra.currentPeriod
		self.fixedPeriod = extra.fixedPeriod

	def __repr__(self):
		return str(self.__dict__)

def getRecordDict(fp):
	recordDict = {}
	with fp:
		for line in fp:
			line = line.strip()
			if line.startswith("#"):
				continue

			arr = re.split(' +', line)
			if len(arr) != 8:
				print("非法数据,长度不对：", len(arr), line)
				exit()

			if arr[2] in recordDict:
				recordDict.get(arr[2]).merge(arr)
			else:
				recordDict[arr[2]] = Record(arr)
	return recordDict


class RecordExtra(Record):
	# 010001  19809.00  2017-5-1 2019-8-1 20 1
	def __init__(self, arr):
		self.code = arr[0]
		self.income = float(arr[1])
		self.startTime = datetime.strptime(arr[2], "%Y-%m-%d")
		self.endTime = datetime.strptime(arr[3], "%Y-%m-%d")
		self.periods = int(arr[4])
		self.currentPeriod = int(arr[5])
		self.fixedPeriod = self.currentPeriod
		if self.currentPeriod > self.periods or self.periods < 1 or self.currentPeriod < 1:
			print("非法数据,分期数不对：", arr)
			exit()
		self.valid()

	def valid(self):
		now = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), "%Y-%m-%d")
		days = int((self.endTime - self.startTime).days * self.fixedPeriod / self.periods)
		predictDay = self.startTime + timedelta(days=days)
		# print(" haha ", (self.endTime - self.startTime).days, ", self.fixedPeriod: " , self.fixedPeriod )
		# print("predictDay >= now:", predictDay, ", ",  theDay, ", days: " , days )
		if predictDay < now:
			print("公司已经失效了： ", self)
			exit()


	def __repr__(self):
		return str(self.__dict__)

def getRecordExtraDict(fp):
	recordExtraDict = {}
	with fp:
		for line in fp:
			line = line.strip()
			if line.startswith("#"):
				continue

			arr = re.split(' +', line)
			if len(arr) != 6:
				print("非法数据,长度不对：", len(arr), line)
				exit()

			if arr[0] in recordExtraDict:
				print("非法数据-一个公司有重复数据：", line)
				exit()
			else:
				recordExtraDict[arr[0]] = RecordExtra(arr)

	return recordExtraDict


def mergeRecordExtra(dict, extraDict):
	for k, v in extraDict.items():
		if k not in dict:
			print("extra的数据竟然没有原始订单, code: ", k)
			exit()
		dict[k].mergeExtra(v)

#
# Entry point 
#
if __name__ == "__main__" :
	
	parser = argparse.ArgumentParser(description='Description of your program')
	parser.add_argument('-r','--recordfile', help='订单信息', required=True, type=argparse.FileType('r'))
	parser.add_argument('-i','--instalment', help='分期付款', required=True, type=argparse.FileType('r'))
	parser.add_argument('-y','--year', help='预测n年', required=False, type=int, default=1)
	args = vars(parser.parse_args())
	# print(args)

	recordDict = getRecordDict(args['recordfile'])
	recordExtraDict = getRecordExtraDict(args['instalment'])

	mergeRecordExtra(recordDict, recordExtraDict)

	now = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), "%Y-%m-%d")
	print(now)

	for day in range(args['year']*365):
		theDay = now + timedelta(days=day)
		for k in recordDict:
			futureRecord = recordDict[k].predict(theDay)
			if futureRecord is not None:
				print(futureRecord)




