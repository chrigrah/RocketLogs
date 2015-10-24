import tkinter
import tkinter.messagebox
import re
import os
import pickle
import matplotlib
matplotlib.use("TkAgg");

import matplotlib.backends.backend_tkagg as mpltk
import matplotlib.figure as mplfig

FONT = ("Verdana", 12);

ROW_UNRANKED = 1
ROW_RANKED_DUEL = 2
ROW_RANKED_DOUBLES = 3
ROW_RANKED_SOLO_STANDARD = 4
ROW_RANKED_STANDARD = 5

playlistMap = {
	ROW_UNRANKED: 0,
	ROW_RANKED_DUEL: 10,
	ROW_RANKED_DOUBLES: 11,
	ROW_RANKED_SOLO_STANDARD: 12,
	ROW_RANKED_STANDARD: 13,
};

playlistToRow = {
	0: ROW_UNRANKED,
	10: ROW_RANKED_DUEL,
	11: ROW_RANKED_DOUBLES,
	12: ROW_RANKED_SOLO_STANDARD,
	13: ROW_RANKED_STANDARD,
};

class Row():
	mu = None;
	sigma = None;
	mmr = None;
	mmrDiffLabel = None;

	def __init__(self, master):
		self.mu = tkinter.StringVar(master, "N/A");
		self.sigma = tkinter.StringVar(master, "N/A");
		self.mmr = tkinter.StringVar(master, "N/A");
		self.mmrDiff = tkinter.StringVar(master, "N/A");

	def setMu(self, value):
		self.mu.set(value);

	def setSigma(self, value):
		self.sigma.set(value);

	def setMmr(self, value):
		self.mmr.set(value);

	def setMmrDiff(self, value, c):
		self.mmrDiffLabel.config(text=value, fg=c);

class MmrFrame(tkinter.Frame):
	rows = {};
	plot = None;
	radioVar = None;
	plotSizeRadioVar = None;
	data = { 0: [], 10: [], 11: [], 12: [], 13: [] };
	lastDataPoint = { 0: None, 10: None, 11: None, 12: None, 13: None };
	canvas = None;

	MMR_PICKLE_VERSION = 1;

	def pickle(self, pFile):
		pickle.dump(self.MMR_PICKLE_VERSION, pFile);
		pickle.dump(self.data, pFile);
		pickle.dump(self.lastDataPoint, pFile);

	def unpickle(self, pFile):
		version = pickle.load(pFile);
		self.data = pickle.load(pFile);
		self.lastDataPoint = pickle.load(pFile);

		for (key, val) in self.lastDataPoint.items():
			if val:
				self.updateRow(val);

	def __init__(self, master=None):
		tkinter.Frame.__init__(self, master);
		#self.grid(row=0, column=0, sticky="nswe");
		self.pack(fill=tkinter.X);
		self.createWidgets();

	def createWidgets(self):
		self.radioVar = tkinter.IntVar(self, 0);

		labelHeader = tkinter.Label(self, text="Playlist", font=("Verdana", 12));
		labelHeader.grid(row=0, column=0, sticky="nsw");
		muHeader = tkinter.Label(self, text="Mu", font=("Verdana", 12));
		muHeader.grid(row=0, column=1, sticky="ns", padx=5);
		sigmaHeader = tkinter.Label(self, text="Sigma", font=("Verdana", 12));
		sigmaHeader.grid(row=0, column=2, sticky="ns", padx=5);
		mmrHeader = tkinter.Label(self, text="TrueSkill", font=("Verdana", 12));
		mmrHeader.grid(row=0, column=3, sticky="ns", padx=5);
		mmrDiffHeader = tkinter.Label(self, text="TS change", font=("Verdana", 12));
		mmrDiffHeader.grid(row=0, column=4, columnspan=2, sticky="ns");

		self.rows[ROW_UNRANKED] = self.addRow("Unranked", ROW_UNRANKED, 0);
		self.rows[ROW_RANKED_DUEL] = self.addRow("Ranked Duel", ROW_RANKED_DUEL, 10);
		self.rows[ROW_RANKED_DOUBLES] = self.addRow("Ranked Doubles", ROW_RANKED_DOUBLES, 11);
		self.rows[ROW_RANKED_SOLO_STANDARD] = self.addRow("Ranked Solo Standard", ROW_RANKED_SOLO_STANDARD, 12);
		self.rows[ROW_RANKED_STANDARD] = self.addRow("Ranked Standard", ROW_RANKED_STANDARD, 13);

		figure = mplfig.Figure(figsize=(5, 3), dpi=100, frameon=False);
		self.plot = figure.add_subplot(1, 1, 1);

		self.canvas = mpltk.FigureCanvasTkAgg(figure, self);
		self.canvas.show();
		self.canvas.get_tk_widget().grid(row=0, column=6, rowspan=6);

		self.plotSizeRadioVar = tkinter.IntVar(self, 20);

		self.createPlotSizeWidgets();


	def createPlotSizeWidgets(self):
		row = 1;
		for x in (10, 20, 50, 100, 0):
			f = tkinter.Frame(self);
			tkLabel = tkinter.Label(f, text=str(x) if x != 0 else "All", font=("Verdana", 10));
			tkLabel.pack(side=tkinter.LEFT);
			tkRadio = tkinter.Radiobutton(f, variable=self.plotSizeRadioVar, value=x, command=self.update);
			tkRadio.pack(side=tkinter.LEFT);
			f.grid(row=row, column=7);

			row += 1;

	def addRow(self, label, row, playlistId):
		rowObject = Row(self);

		tkLabel = tkinter.Label(self, text=label, font=("Verdana", 10));
		tkLabel.grid(row=row, column=0, sticky="nsw");
		tkMu = tkinter.Label(self, textvariable=rowObject.mu, font=("Verdana", 10));
		tkMu.grid(row=row, column=1, sticky="nse");
		tkSigma = tkinter.Label(self, textvariable=rowObject.sigma, font=("Verdana", 10));
		tkSigma.grid(row=row, column=2, sticky="nse");
		tkMmr = tkinter.Label(self, textvariable=rowObject.mmr, fg="green", font=("Verdana", 11));
		tkMmr.grid(row=row, column=3, sticky="nse");
		rowObject.mmrDiffLabel = tkinter.Label(self, text="N/A", fg="yellow", font=("Verdana", 10));
		rowObject.mmrDiffLabel.grid(row=row, column=4, sticky="nse");

		tkRadio = tkinter.Radiobutton(self, variable=self.radioVar, value=playlistId, command=self.update);
		tkRadio.grid(row=row, column=5);

		return rowObject;

	def updateMu(self, row, value):
		self.rows[row].setMu("{:1.3f}".format(value));

	def updateSigma(self, row, value):
		self.rows[row].setSigma("{:1.3f}".format(value));

	def updateMmr(self, row, value):
		self.rows[row].setMmr("{:1.3f}".format(value));

	def updateMmrDiff(self, row, value):
		self.rows[row].setMmrDiff("{:+1.3f}".format(value), "green" if value > 0 else "red");

	def addDataPoint(self, point):
		if point['Playlist'] in (1, 2, 3, 4):
			point['Playlist'] = 0;

		pl = point['Playlist'];
		trueSkill = point['Mu'] - 3 * point['Sigma'];
		self.data[pl].append(trueSkill);

		self.updateRow(point);
		self.lastDataPoint[pl] = point;

	def updateRow(self, point):
		pl = point['Playlist'];
		trueSkill = point['Mu'] - 3 * point['Sigma'];

		self.updateMu(playlistToRow[pl], point['Mu'])
		self.updateSigma(playlistToRow[pl], point['Sigma'])
		self.updateMmr(playlistToRow[pl], trueSkill)
		if len(self.data[pl]) > 1:
			self.updateMmrDiff(playlistToRow[pl], trueSkill - self.data[pl][-2]);

	def update(self):
		plotPlaylist = self.radioVar.get();
		plotSize = self.plotSizeRadioVar.get();

		data = None;
		if plotSize == 0:
			data = self.data[plotPlaylist]
		else:
			data = self.data[plotPlaylist][-plotSize:];

		self.plot.clear();
		self.plot.plot(data);
		self.plot.relim();
		self.plot.autoscale_view(tight=False);
		self.canvas.draw();

findMmrLineRegex = re.compile("ClientSetSkill Playlist=([0-9]+) Mu=([0-9.]+) Sigma=([0-9.]+)");
def update(mmr):
	global logFileSize;
	# Crude check to see if rocket league has restarted, which resets the log.
	currentSize = os.fstat(logFile.fileno()).st_size;
	if currentSize < logFileSize:
		logFile.seek(0);
		print ("Log reset. Starting over.");
	logFileSize = currentSize;

	for line in logFile:
		# TrueSkill data
		trueskillData = findMmrLineRegex.search(line);
		if trueskillData:
			print("Found skillmu line. playlist=%d, mu=%f, sigma=%f" % (int(trueskillData.group(1)), float(trueskillData.group(2)), float(trueskillData.group(3))));
			dataPoint = {
				'Playlist': int(trueskillData.group(1)),
				'Mu': float(trueskillData.group(2)),
				'Sigma': max(2.5, float(trueskillData.group(3)))
			};
			mmr.addDataPoint(dataPoint);

	mmr.update();

	mmr.after(2000, update, mmr);

logFile = None;
logFileSize = 0;
def openLog():
	try:
		global logFile;
		logFile = open('../Launch.log', mode='r');
	except:
		tkinter.messagebox.showerror("Failed to open Launch.log", "The program could not open Launch.log. Please place the program at Documents/My Games/Rocket League/TAGame/Logs/RocketLogs/.");
		raise

def getLogSignature():
	offset = logFile.tell();
	logFile.seek(0);
	sig = logFile.readline();
	logFile.seek(offset);
	return sig;

def openHistory(openMode):
	try:
		return open('history.dat', mode=openMode);
	except:
		tkinter.messagebox.showerror("Failed to open history.dat :(");
		raise

############################################################################################################
openLog();

lastLogSignature = None;
lastLogOffset = 0;


master = tkinter.Tk();
master.wm_title("RocketLogs v0.1.0");
masterFrame = tkinter.Frame(master);
masterFrame.pack();
mmr = MmrFrame(masterFrame);

try:
	historyFile = open('history.dat', mode='rb');
	lastLogSignature = pickle.load(historyFile);
	lastLogOffset = pickle.load(historyFile);
	mmr.unpickle(historyFile);
	historyFile.close();
except:
	print("No history.dat found. Continuing without history.");

currentLogSignature = getLogSignature();
if currentLogSignature == lastLogSignature:
	logFile.seek(lastLogOffset);

try:
	update(mmr);
	master.mainloop();
finally:
	historyFile = open('history.dat', mode='wb');
	pickle.dump(getLogSignature(), historyFile);
	pickle.dump(logFile.tell(), historyFile);
	mmr.pickle(historyFile);
	historyFile.close();

logFile.close();