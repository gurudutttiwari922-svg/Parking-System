# parking_system/gui_visual.py
import os, json, tkinter as tk
from datetime import datetime, timezone
from tkinter import messagebox, simpledialog
from parking_system.core import ParkingLot, Vehicle
from parking_system.persistence import load_parking, save_parking

DATA, HIST, REFRESH = "sample_data.json", "history.json", 1500
C = {'bg':'#f9fafb','hdr':'#263238','pnl':'#fff','txt':'#000','pass':'#d7ccc8','bd':'#9e9e9e',
     '4W_e':'#fff59d','4W_o':'#f57c00','2W_e':'#81d4fa','2W_o':'#0288d1','TR_e':'#ffcc80','TR_o':'#ef6c00'}

def now(): return datetime.now(timezone.utc).isoformat()
def hist(ev):
    d=json.load(open(HIST)) if os.path.exists(HIST) else []
    d.append(ev); json.dump(d[-200:],open(HIST,'w'),indent=2)

class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Parking Management System")
        self.geometry("1450x830"); self.configure(bg=C['bg'])
        self.pl = load_parking(DATA) or ParkingLot({'4W':120,'2W':144,'TR':48})
        self.res,self.visual,self.slots=set(),{},{}
        self.panel_visible=True
        self._ui()
        self._layout()
        self.after(REFRESH,self._refresh)

    # UI 
    def _ui(self):
        tk.Label(self,text="🚗 Smart Parking Management System",bg=C['hdr'],fg='white',
                 font=("Segoe UI",18,'bold')).pack(fill='x')
        body=tk.Frame(self,bg=C['bg']); body.pack(fill='both',expand=True)

        # scrollable canvas
        self.canvas_frame = tk.Frame(body,bg=C['bg'])
        self.canvas_frame.pack(side='left',fill='both',expand=True,padx=5,pady=5)
        self.canvas = tk.Canvas(self.canvas_frame,bg=C['bg'],highlightthickness=0,scrollregion=(0,0,1600,1000))
        self.hbar = tk.Scrollbar(self.canvas_frame,orient='horizontal',command=self.canvas.xview)
        self.vbar = tk.Scrollbar(self.canvas_frame,orient='vertical',command=self.canvas.yview)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.grid(row=0,column=0,sticky='nsew')
        self.hbar.grid(row=1,column=0,sticky='we')
        self.vbar.grid(row=0,column=1,sticky='ns')
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # Toggle panel button
        self.toggle_btn=tk.Button(self,text="⮜ Hide Panel",command=self._toggle, bg='#607D8B',fg='white',relief='flat')
        self.toggle_btn.place(relx=0.985,rely=0.012,anchor='ne')

        self.panel=tk.Frame(body,width=300,bg=C['pnl']); self.panel.pack(side='right',fill='y',padx=(8,0))
        self._panel(); self._footer()

    def _panel(self):
        self.l4=tk.Label(self.panel,bg=C['pnl']); self.l2=tk.Label(self.panel,bg=C['pnl']); self.lt=tk.Label(self.panel,bg=C['pnl'])
        [l.pack(anchor='w',padx=10,pady=2) for l in (self.l4,self.l2,self.lt)]
        tk.Label(self.panel,text="\nLegend:",bg=C['pnl'],font=('Segoe UI',10,'bold')).pack(anchor='w',padx=10)
        for t,name in [("4W","Car"),("2W","Bike"),("TR","Truck")]:
            col = C[f"{t}_e"]
            f=tk.Frame(self.panel,bg=C['pnl']); f.pack(anchor='w',padx=15)
            tk.Label(f,width=2,height=1,bg=col,relief='solid').pack(side='left',padx=3)
            tk.Label(f,text=f"{t} — {name}",bg=C['pnl']).pack(side='left')
        tk.Label(self.panel,text="\nSearch Vehicle:",bg=C['pnl']).pack(anchor='w',padx=10)
        self.sv=tk.StringVar(); e=tk.Entry(self.panel,textvariable=self.sv,width=25); e.pack(padx=10,pady=4)
        e.bind("<Return>",lambda _:self._search())
        tk.Button(self.panel,text="Search",command=self._search).pack(pady=2)
        tk.Button(self.panel,text="Show History",command=self._hist).pack(pady=4)
        tk.Button(self.panel,text="Save State",command=self._save).pack(pady=4)

    def _footer(self):
        f=tk.Frame(self,bg=C['bg']); f.pack(fill='x')
        tk.Label(f,text="Click slot = Park/Unpark | Ctrl+Click = Reserve",bg=C['bg']).pack(side='left',padx=8)
        self.clock=tk.Label(f,bg=C['bg']); self.clock.pack(side='right',padx=8); self._clk()

    def _clk(self):
        self.clock.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S")); self.after(1000,self._clk)

    # Layout 
    def _layout(self):
        self.canvas.delete("all"); self.visual.clear(); self.slots.clear()
        cW,cH,bW,bH,tW,tH,sp=28,22,22,20,34,28,8
        lm = 60
        ox = lm + 2*(tW+sp) + 50
        oy = 60

        def slot(vt,lbl,x,y,w,h,idx):
            v=self.pl.slots.get(vt,{}).get(idx); f=C[f"{vt}_{'o' if v else 'e'}"]
            if (vt,idx) in self.res and not v:f="#ffd8a8"
            r=self.canvas.create_rectangle(x,y,x+w,y+h,fill=f,outline=C['bd'])
            t=self.canvas.create_text(x+w/2,y+h/2,text=(v.number[:6] if v else lbl),
                                   font=("Segoe UI",8,"bold"),fill=C['txt'])
            self.visual[lbl]=(vt,idx); self.slots[lbl]=(r,t)
            for tag in (r,t): self.canvas.tag_bind(tag,"<Button-1>",lambda e,l=lbl:self._click(e,l))

        # Vertical passages
        pass_w = 24
        self.canvas.create_rectangle(lm+2*(tW+sp)+10, oy-10, lm+2*(tW+sp)+10+pass_w, 600, fill=C['pass'], outline='')
        self.canvas.create_text(lm+2*(tW+sp)+10+pass_w/2, 300, text="\n".join("PASSAGE"), font=("Segoe UI",8,"bold"))
        ex = ox + 30*(cW+sp) + (lm + 2*(tW+sp))
        self.canvas.create_rectangle(ex-pass_w-2, oy-10, ex, 600, fill=C['pass'], outline='')
        self.canvas.create_text(ex-pass_w/2-2, 300, text="\n".join("PASSAGE"), font=("Segoe UI",8,"bold"))

        # Entry/Exit labels
        self.canvas.create_text(lm-10,oy-20,text="ENTRY →",font=("Segoe UI",11,"bold"),fill="green")
        self.canvas.create_text(ex+60,oy+530,text="← EXIT",font=("Segoe UI",11,"bold"),fill="red")

        # Left D (12×2)
        d=1
        for c in range(2):
            for r in range(12):
                slot('TR',f"D{d}",lm+c*(tW+sp),oy+r*(tH+sp),tW,tH,d); d+=1

        # A top 2×30
        a=1
        for r in range(2):
            for c in range(30):
                slot('4W',f"A{a}",ox+c*(cW+sp),oy+r*(cH+sp),cW,cH,a); a+=1
        py=oy+2*(cH+sp)+8; self._pass(ox-5,py,30*(cW+sp)+10,"ENTRY")

        # C middle 6×24 with passage after every 2 columns
        bc,br,gc,pw=24,6,2,24; cy=py+60
        total_bw=bc*(bW+sp)+((bc//gc)-1)*pw
        offset=int((30*(cW+sp)-total_bw)/2)

        for g in range(1,bc//gc):
            px=ox+offset+g*gc*(bW+sp)+(g-1)*pw; ph=br*(bH+sp)+8
            self.canvas.create_rectangle(px-2,cy-4,px+pw,cy+ph,fill=C['pass'],outline='')
            self.canvas.create_text(px+pw/2,cy+ph/2,text="\n".join("PASSAGE"),
                                 font=("Segoe UI",8,"bold"),fill=C['txt'])

        ci=1
        for r in range(br):
            for c in range(bc):
                ex2=(c//gc)*pw; slot('2W',f"C{ci}",ox+offset+c*(bW+sp)+ex2,cy+r*(bH+sp),bW,bH,ci); ci+=1

        py2=cy+br*(bH+sp)+10; self._pass(ox-5,py2,30*(cW+sp)+10,"PASSAGE")

        # B bottom
        b=1; by=py2+50
        for r in range(2):
            for c in range(30):
                slot('4W',f"B{b}",ox+c*(cW+sp),by+r*(cH+sp),cW,cH,60+b); b+=1
        exitY=by+2*(cH+sp)+10; self._pass(ox-5,exitY,30*(cW+sp)+10,"EXIT PASSAGE")

        # Right E (mirror D)
        e=1
        for c in range(2):
            for r in range(12):
                slot('TR',f"E{e}",ex+c*(tW+sp),oy+r*(tH+sp),tW,tH,20+e); e+=1
        self._status()

    def _pass(self,x,y,w,t):
        self.canvas.create_rectangle(x,y,x+w,y+22,fill=C['pass'],outline='')
        self.canvas.create_text(x+w/2,y+11,text=t,font=("Segoe UI",10,"bold"),fill=C['txt'])

    def _click(self,e,lbl):
        ctrl=(e.state&0x4)!=0; vt,idx=self.visual[lbl]
        if ctrl:self.res.symmetric_difference_update({(vt,idx)}); self._layout(); return
        v=self.pl.slots[vt].get(idx)
        if not v:
            num=simpledialog.askstring("Park",f"Vehicle for {lbl}:")
            if not num:return
            self.pl.slots[vt][idx]=Vehicle(num.strip().upper(),vt,now())
            save_parking(DATA,self.pl); hist({'event':'park','vehicle':num,'slot':lbl,'time':now()})
        else:
            if not messagebox.askyesno("Remove",f"Remove {v.number}?"):return
            ok,_,fee=self.pl.remove_vehicle(f"{vt}-{idx}")
            if ok: save_parking(DATA,self.pl); hist({'event':'remove','vehicle':v.number,'slot':lbl,'time':now(),'fee':fee})
            messagebox.showinfo("Removed",f"{v.number} removed\nFee: {fee}")
        self._layout()

    def _toggle(self):
        if self.panel_visible:
            self.panel.pack_forget(); self.panel_visible=False; self.toggle_btn.config(text="⮞ Show Panel")
        else:
            self.panel.pack(side='right',fill='y',padx=(8,0)); self.panel_visible=True; self.toggle_btn.config(text="⮜ Hide Panel")

    def _status(self):
        st=self.pl.status_summary()
        def occ(k): return round((st[k]['occupied']/st[k]['total'])*100,1)
        self.l4.config(text=f"4W: {st['4W']['occupied']}/{st['4W']['total']} ({occ('4W')}%)")
        self.l2.config(text=f"2W: {st['2W']['occupied']}/{st['2W']['total']} ({occ('2W')}%)")
        self.lt.config(text=f"TR: {st['TR']['occupied']}/{st['TR']['total']} ({occ('TR')}%)")

    def _search(self):
        t=self.sv.get().strip().upper()
        if not t:return messagebox.showinfo("Search","Enter vehicle number")
        f=self.pl.find_vehicle(t)
        if not f:return messagebox.showinfo("Search",f"{t} not found")
        vt,idx=f
        for lbl,(v2,i2) in self.visual.items():
            if (vt,idx)==(v2,i2): messagebox.showinfo("Found",f"{t} at {lbl} ({vt}:{idx})"); break

    def _hist(self):
        if not os.path.exists(HIST):return messagebox.showinfo("History","No data")
        d=json.load(open(HIST))[-20:]; w=tk.Toplevel(self); w.title("History")
        t=tk.Text(w,width=70,height=20); t.pack()
        t.insert("1.0","\n".join(f"{h['time'][:19]} | {h['event']} | {h.get('vehicle','')}" for h in d))
        t.config(state='disabled')

    def _save(self): save_parking(DATA,self.pl); messagebox.showinfo("Saved","State saved")

    def _refresh(self):
        for lbl,(r,t) in self.slots.items():
            vt,idx=self.visual[lbl]; v=self.pl.slots[vt].get(idx)
            f=C[f"{vt}_{'o' if v else 'e'}"]
            if (vt,idx) in self.res and not v:f="#ffd8a8"
            self.canvas.itemconfig(r,fill=f); self.canvas.itemconfig(t,text=(v.number[:6] if v else lbl))
        self._status(); self.after(REFRESH,self._refresh)

if __name__=="__main__":
    GUI().mainloop()
