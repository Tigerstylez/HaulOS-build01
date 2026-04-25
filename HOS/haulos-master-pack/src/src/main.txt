
      icon: <AlertTriangle className="w-16 h-16 text-red-500" />
    },
    {
      title: "The Solution",
      subtitle: "Every Truck is a Sensor",
      content: "A real-time network where driver pings inform the whole fleet.",
      points: [
        "Constraint-Aware Routing (WA-First)",
        "Fuel Intelligence (Availability + Confidence)",
        "One-Tap Hazard Reporting",
        "Escort Mode for Oversize Loads (Phase 2)"
      ],
      icon: <Zap className="w-16 h-16 text-yellow-500" />
    },
    {
      title: "Fuel Intelligence",
      subtitle: "The Hook for Daily Retention",
      content: "During WA fuel shortages, availability isn't just data—it's survival.",
      stats: [
        { label: "Confidence", val: "Multi-user verification" },
        { label: "Real-time", val: "2-4 hour auto-expiry" },
        { label: "Actionable", val: "Route-based risk alerts" }
      ],
      icon: <Fuel className="w-16 h-16 text-blue-400" />
    },
    {
      title: "Business Model",
      subtitle: "Scalable SaaS & Data Layer",
      content: "Targeting a $1.5M pre-money valuation with a high-moat network effect.",
      points: [
        "Driver Subscription: Freemium to Premium",
        "Fleet Subscription: Per-vehicle enterprise billing",
        "Data API: Government & Logistics partnerships",
        "Current Raise: $200k AUD for 12% equity"
      ],
      icon: <TrendingUp className="w-16 h-16 text-emerald-500" />
    }
  ];

  const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % slides.length);
  const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);

  // --- SUB-VIEWS ---

  const SlideView = () => {
    const s = slides[currentSlide];
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 text-center animate-in fade-in duration-700">
        <div className="mb-6">{s.icon}</div>
        <h1 className="text-4xl md:text-6xl font-black text-white mb-2 italic tracking-tighter uppercase">{s.title}</h1>
        <h2 className="text-xl md:text-2xl text-blue-400 mb-8 font-semibold">{s.subtitle}</h2>
        {s.content && <p className="max-w-2xl text-slate-300 text-lg mb-8">{s.content}</p>}
        {s.points && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left max-w-4xl w-full">
            {s.points.map((p, i) => (
              <div key={i} className="flex items-center space-x-3 bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <CheckCircle2 className="w-5 h-5 text-blue-500 shrink-0" />
                <span className="text-slate-200 font-medium">{p}</span>
              </div>
            ))}
          </div>
        )}
        {s.stats && (
          <div className="flex flex-wrap justify-center gap-4 w-full">
            {s.stats.map((st, i) => (
              <div key={i} className="bg-slate-900 border border-slate-700 p-6 rounded-2xl min-w-[180px]">
                <div className="text-blue-400 font-black text-[10px] uppercase tracking-widest mb-1">{st.label}</div>
                <div className="text-white text-lg font-bold">{st.val}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const PrototypeView = () => {
    return (
      <div className="flex flex-col md:flex-row items-center justify-center gap-12 py-4">
        {/* Device Frame */}
        <div className="relative w-[340px] h-[680px] bg-black rounded-[3rem] border-[10px] border-slate-800 shadow-2xl overflow-hidden">
          
          {/* Mock Status Bar */}
          <div className="absolute top-0 left-0 right-0 h-10 bg-black z-[100] flex items-center justify-between px-8 pt-2">
            <span className="text-[10px] text-white font-bold">9:41</span>
            <div className="flex space-x-1 items-center">
              <div className="w-3 h-3 rounded-full bg-white opacity-20"></div>
              <div className="w-5 h-2.5 bg-white rounded-sm"></div>
            </div>
          </div>

          {appStep === 'setup' ? (
            <div className="h-full bg-slate-950 flex flex-col p-6 pt-20">
              <h2 className="text-2xl font-black text-white italic tracking-tighter mb-2">VEHICLE SETUP</h2>
              <p className="text-slate-400 text-sm mb-8">Dimensions required for WA road network compliance.</p>
              <div className="space-y-4 mb-auto">
                {['Height', 'Weight', 'Length'].map((label) => (
                  <div key={label} className="bg-slate-900 p-4 rounded-xl border border-slate-800">
                    <label className="text-[10px] text-slate-500 font-bold uppercase block mb-1">{label}</label>
                    <span className="text-white font-bold">{vehicle[label.toLowerCase()]} {label === 'Weight' ? 't' : 'm'}</span>
                  </div>
                ))}
              </div>
              <button 
                onClick={() => setAppStep('main')}
                className="w-full bg-blue-600 py-4 rounded-2xl font-black text-white flex items-center justify-center space-x-2 active:scale-95 transition shadow-lg shadow-blue-500/20"
              >
                <span>ENTER NETWORK</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <div className="h-full flex flex-col bg-slate-950 relative">
              {/* Internal App Header */}
              <div className="h-16 bg-slate-900/90 backdrop-blur-md flex items-center justify-between px-4 pt-4 border-b border-slate-800 z-50">
                <div className="flex items-center space-x-2">
                   <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center text-[10px] font-black italic">H</div>
                   <span className="text-white font-black tracking-tighter text-sm uppercase">HAULOS</span>
                </div>
                <div className="flex space-x-3">
                  <Bell className="w-4 h-4 text-slate-400" />
                  <Settings className="w-4 h-4 text-slate-400" />
                </div>
              </div>

              {/* Dynamic Map/Log View */}
              <div className="flex-1 relative">
                {activeTab === 'map' && (
                  <div className="h-full w-full bg-slate-900 relative">
                    <div className="absolute inset-0 opacity-10" style={{backgroundImage: 'radial-gradient(#fff 1px, transparent 0)', backgroundSize: '30px 30px'}} />
                    <svg className="absolute inset-0 w-full h-full opacity-40">
                      <path d="M 170 600 L 170 300 L 300 100" fill="none" stroke="#3B82F6" strokeWidth="4" strokeDasharray="8,4" />
                    </svg>
                    {/* Interaction Markers */}
                    <div className="absolute top-[40%] left-[30%]">
                       <div className="bg-red-500 p-1.5 rounded-full shadow-lg animate-bounce">
                          <Fuel className="w-3 h-3 text-white" />
                       </div>
                    </div>
                  </div>
                )}
                
                {activeTab === 'log' && (
                  <div className="h-full bg-slate-950 p-6 flex flex-col">
                    <h3 className="text-white font-black text-xl mb-4 italic uppercase">Digital Logbook</h3>
                    <div className="bg-slate-900 rounded-3xl p-8 text-center border border-slate-800 mb-6">
                       <div className="text-4xl font-mono text-blue-500 mb-2">{formatTime(logTimer)}</div>
                       <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Drive Session</div>
                    </div>
                    <button 
                      onClick={() => { setLogbookActive(!logbookActive); addNotification(logbookActive ? "Break Started" : "Drive Resumed") }}
                      className={`w-full py-4 rounded-2xl font-bold flex items-center justify-center space-x-2 ${logbookActive ? 'bg-orange-500/20 text-orange-400 border border-orange-500/40' : 'bg-emerald-500 text-white'}`}
                    >
                      {logbookActive ? <Clock className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      <span>{logbookActive ? 'START 15m REST' : 'RESUME DRIVE'}</span>
                    </button>
                  </div>
                )}

                {/* Reporting Modal Overlay */}
                {activeTab === 'fuel' && (
                  <div className="absolute inset-0 bg-slate-950/95 z-[70] p-6 pt-16 animate-in slide-in-from-bottom duration-300">
                    <div className="flex justify-between items-center mb-6 text-white font-black italic">
                      <h3 className="uppercase">Report Fuel</h3>
                      <X className="text-slate-500 cursor-pointer" onClick={() => setActiveTab('map')} />
                    </div>
                    <div className="space-y-3">
                      {['AVAILABLE', 'LOW SUPPLY', 'NO DIESEL', 'CLOSED'].map(status => (
                        <button 
                          key={status}
                          onClick={() => { addNotification(`Reported: ${status}`); setActiveTab('map'); }}
                          className="w-full bg-slate-900 p-4 rounded-2xl text-white font-bold text-xs text-left border border-slate-800 hover:bg-blue-600 transition"
                        >
                          {status}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Navigation Bar */}
              <div className="h-20 bg-slate-900 border-t border-slate-800 flex items-center justify-around px-2 pb-4">
                 <button onClick={() => setActiveTab('map')} className={`flex flex-col items-center ${activeTab === 'map' ? 'text-blue-500' : 'text-slate-500'}`}>
                    <MapIcon className="w-5 h-5" />
                    <span className="text-[8px] font-bold mt-1 uppercase">Map</span>
                 </button>
                 <button onClick={() => setActiveTab('fuel')} className={`flex flex-col items-center ${activeTab === 'fuel' ? 'text-blue-500' : 'text-slate-500'}`}>
                    <Fuel className="w-5 h-5" />
                    <span className="text-[8px] font-bold mt-1 uppercase">Fuel</span>
                 </button>
                 <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center -mt-8 shadow-xl shadow-blue-500/40 active:scale-90 transition cursor-pointer" 
                      onClick={() => addNotification("Emergency Beacon Activated", 'danger')}>
                    <AlertTriangle className="text-white w-6 h-6" />
                 </div>
                 <button onClick={() => setActiveTab('log')} className={`flex flex-col items-center ${activeTab === 'log' ? 'text-blue-500' : 'text-slate-500'}`}>
                    <FileText className="w-5 h-5" />
                    <span className="text-[8px] font-bold mt-1 uppercase">Log</span>
                 </button>
                 <button className="flex flex-col items-center text-slate-500"><Shield className="w-5 h-5" /><span className="text-[8px] font-bold mt-1 uppercase">Escort</span></button>
              </div>

              {/* Notification Overlay */}
              <div className="absolute top-20 left-4 right-4 space-y-2 pointer-events-none z-[80]">
                {notifications.map(n => (
                  <div key={n.id} className="bg-white rounded-xl p-3 shadow-2xl flex items-center space-x-3 animate-in slide-in-from-top-4 duration-300">
                    <Info className={`w-4 h-4 ${n.type === 'danger' ? 'text-red-600' : 'text-blue-600'}`} />
                    <p className="text-slate-900 text-[10px] font-bold">{n.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="max-w-xs space-y-6">
          <div className="bg-slate-900 p-6 rounded-3xl border border-slate-800">
            <h3 className="text-white font-bold mb-2 flex items-center space-x-2">
              <Code className="text-blue-400 w-4 h-4" />
              <span>Technical Demo</span>
            </h3>
            <p className="text-slate-400 text-sm leading-relaxed mb-4 italic">
              "Every truck is a sensor on the road."
            </p>
            <div className="space-y-2">
              <button 
                onClick={() => { setAppStep('setup'); setActiveTab('map'); }}
                className="w-full bg-slate-800 text-xs py-2 rounded-lg text-slate-300 hover:text-white transition uppercase font-bold"
              >
                Reset Setup
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-blue-500/30">
      {/* Universal Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-[100] border-b border-slate-900 bg-slate-950/80 backdrop-blur-xl px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => {setCurrentView('deck'); setCurrentSlide(0);}}>
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center font-black text-white italic text-xl shadow-lg shadow-blue-500/20">H</div>
            <div className="leading-none">
              <span className="text-xl font-black tracking-tighter text-white block italic">HAULOS</span>
              <span className="text-[10px] text-blue-500 font-black tracking-widest uppercase">MASTER PACK</span>
            </div>
          </div>
          
          <div className="flex bg-slate-900/50 p-1 rounded-2xl border border-slate-800">
            <button 
              onClick={() => setCurrentView('deck')}
              className={`px-6 py-2 rounded-xl text-xs font-black transition-all ${currentView === 'deck' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' : 'text-slate-500 hover:text-white'}`}
            >
              INVESTOR DECK
            </button>
            <button 
              onClick={() => setCurrentView('prototype')}
              className={`px-6 py-2 rounded-xl text-xs font-black transition-all ${currentView === 'prototype' ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' : 'text-slate-500 hover:text-white'}`}
            >
              PROTOTYPE
            </button>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <main className="pt-28 pb-32 px-6 max-w-7xl mx-auto flex items-center justify-center min-h-[70vh]">
        {currentView === 'deck' ? <SlideView /> : <PrototypeView />}
      </main>

      {/* Footer Controls for Pitch Mode */}
      {currentView === 'deck' && (
        <div className="fixed bottom-10 left-0 right-0 z-[100] flex justify-center">
          <div className="flex items-center space-x-8 bg-slate-900/90 backdrop-blur-xl border border-slate-800 p-3 rounded-3xl shadow-2xl">
             <button disabled={currentSlide === 0} onClick={prevSlide} className="p-2 text-slate-400 hover:text-white disabled:opacity-20 transition-colors"><ChevronLeft className="w-6 h-6" /></button>
             <div className="flex space-x-2">{slides.map((_, i) => <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${i === currentSlide ? 'w-8 bg-blue-500' : 'w-1.5 bg-slate-700'}`} />)}</div>
             <button disabled={currentSlide === slides.length - 1} onClick={nextSlide} className="p-2 text-slate-400 hover:text-white disabled:opacity-20 transition-colors"><ChevronRight className="w-6 h-6" /></button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;