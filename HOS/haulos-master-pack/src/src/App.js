import React, { useState, useEffect } from 'react';
import { 
  Map as MapIcon, 
  Fuel, 
  AlertTriangle, 
  Truck, 
  Navigation, 
  Layout, 
  Code, 
  TrendingUp, 
  Menu, 
  X, 
  ChevronRight, 
  ChevronLeft, 
  Info,
  Layers,
  Zap,
  Shield,
  Clock,
  CheckCircle2,
  Database,
  Smartphone,
  Scale,
  Ruler,
  Maximize,
  ArrowRight,
  Settings,
  Bell,
  FileText
} from 'lucide-react';

const App = () => {
  const [currentView, setCurrentView] = useState('deck');
  const [currentSlide, setCurrentSlide] = useState(0);
  const [appStep, setAppStep] = useState('setup');
  const [vehicle, setVehicle] = useState({ height: '4.3', weight: '22.5', length: '19.0', width: '2.5' });
  const [activeTab, setActiveTab] = useState('map');
  const [notifications, setNotifications] = useState([]);
  const [logbookActive, setLogbookActive] = useState(false);
  const [logTimer, setLogTimer] = useState(0);

  const addNotification = (text, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [{ id, text, type }, ...prev]);
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 4000);
  };

  useEffect(() => {
    let interval;
    if (logbookActive) interval = setInterval(() => setLogTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, [logbookActive]);

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const slides = [
    { title: "HaulOS", subtitle: "Operating System for Heavy Transport", content: "A driver-first intelligence network for Australia's heaviest routes.", icon: <Truck className="w-20 h-20 text-blue-500" />, type: "hero" },
    { title: "The Problem", subtitle: "Drivers Are Operating Blind", points: ["Zero fuel visibility", "Hazards discovered too late", "Non-compliant routing", "Manager-centric tools"], icon: <AlertTriangle className="w-16 h-16 text-red-500" /> },
    { title: "The Solution", subtitle: "Every Truck is a Sensor", content: "Real-time network where driver pings inform the whole fleet.", points: ["Constraint-Aware Routing", "Fuel Intelligence", "One-Tap Hazards", "Escort Mode"], icon: <Zap className="w-16 h-16 text-yellow-500" /> },
    { title: "Fuel Intelligence", subtitle: "The Daily Driver Hook", content: "Know availability before you arrive. 2-tap reporting with confidence scoring.", icon: <Fuel className="w-16 h-16 text-blue-400" /> },
    { title: "The Ask", subtitle: "$200k AUD Raise", content: "Raising for MVP delivery and WA pilot launch (12% Equity).", icon: <TrendingUp className="w-16 h-16 text-emerald-500" /> }
  ];

  const nextSlide = () => setCurrentSlide(c => (c + 1) % slides.length);
  const prevSlide = () => setCurrentSlide(c => (c - 1 + slides.length) % slides.length);

  const Prototype = () => (
    <div className="flex flex-col md:flex-row items-center justify-center gap-8 py-4">
      <div className="relative w-[320px] h-[640px] bg-black rounded-[2.5rem] border-[8px] border-slate-800 shadow-2xl overflow-hidden">
        {appStep === 'setup' ? (
          <div className="h-full bg-slate-950 p-6 pt-16 flex flex-col">
            <h2 className="text-xl font-black text-white italic mb-6">VEHICLE SETUP</h2>
            <div className="space-y-4 mb-auto text-xs">
              {['Height', 'Weight', 'Length'].map(f => (
                <div key={f} className="bg-slate-900 p-4 rounded-xl border border-slate-800">
                  <span className="text-slate-500 font-bold uppercase block mb-1">{f}</span>
                  <span className="text-white font-bold">{vehicle[f.toLowerCase()]} {f === 'Weight' ? 't' : 'm'}</span>
                </div>
              ))}
            </div>
            <button onClick={() => setAppStep('main')} className="w-full bg-blue-600 py-4 rounded-xl font-bold text-white shadow-lg">ENTER NETWORK</button>
          </div>
        ) : (
          <div className="h-full flex flex-col bg-slate-950 relative">
            <div className="h-14 bg-slate-900 flex items-center justify-between px-4 pt-4 border-b border-slate-800">
               <span className="text-white font-black text-xs italic">HAULOS</span>
               <div className="flex space-x-2"><Bell className="w-3 h-3 text-slate-500"/><Settings className="w-3 h-3 text-slate-500"/></div>
            </div>
            <div className="flex-1 relative bg-slate-900">
              <div className="absolute inset-0 opacity-10" style={{backgroundImage: 'radial-gradient(#fff 1px, transparent 0)', backgroundSize: '20px 20px'}}/>
              {activeTab === 'map' && <div className="p-4 text-xs text-blue-400 font-mono italic">Perth Region Active...</div>}
            </div>
            <div className="h-16 bg-slate-900 border-t border-slate-800 flex items-center justify-around pb-2">
              <MapIcon className={`w-5 h-5 ${activeTab === 'map' ? 'text-blue-500' : 'text-slate-600'}`} onClick={() => setActiveTab('map')}/>
              <Fuel className={`w-5 h-5 ${activeTab === 'fuel' ? 'text-blue-500' : 'text-slate-600'}`} onClick={() => setActiveTab('fuel')}/>
              <div className="w-10 h-10 bg-blue-600 rounded-full -mt-6 flex items-center justify-center shadow-lg"><AlertTriangle className="text-white w-5 h-5"/></div>
              <FileText className={`w-5 h-5 ${activeTab === 'log' ? 'text-blue-500' : 'text-slate-600'}`} onClick={() => setActiveTab('log')}/>
              <Shield className="w-5 h-5 text-slate-600"/>
            </div>
            {activeTab === 'fuel' && (
              <div className="absolute inset-0 bg-slate-950 p-6 pt-16 z-[100]">
                <div className="flex justify-between mb-6 items-center"><h3 className="text-white font-bold">REPORT FUEL</h3><X onClick={() => setActiveTab('map')} className="text-slate-500 w-5 h-5"/></div>
                <div className="space-y-2">
                  {['AVAILABLE', 'LOW SUPPLY', 'NO DIESEL'].map(s => (
                    <button key={s} onClick={() => {addNotification(`Reported: ${s}`); setActiveTab('map')}} className="w-full bg-slate-900 p-4 rounded-xl text-white font-bold text-xs text-left hover:bg-blue-600 transition">{s}</button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        {notifications.map(n => (
          <div key={n.id} className="absolute top-16 left-4 right-4 bg-white p-3 rounded-xl shadow-2xl flex items-center space-x-2 z-[200]">
            <Info className="w-4 h-4 text-blue-600"/><p className="text-[10px] font-bold text-slate-900">{n.text}</p>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <nav className="p-4 border-b border-slate-900 flex justify-between items-center max-w-6xl mx-auto">
        <div className="font-black italic text-xl tracking-tighter">HAULOS <span className="text-blue-500 not-italic font-bold text-xs ml-1">MASTER</span></div>
        <div className="flex bg-slate-900 p-1 rounded-xl">
          <button onClick={() => setCurrentView('deck')} className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${currentView === 'deck' ? 'bg-blue-600 text-white' : 'text-slate-500'}`}>DECK</button>
          <button onClick={() => setCurrentView('prototype')} className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${currentView === 'prototype' ? 'bg-blue-600 text-white' : 'text-slate-500'}`}>PROTOTYPE</button>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto p-8 flex items-center justify-center min-h-[70vh]">
        {currentView === 'deck' ? (
          <div className="text-center">
            <div className="mb-6 flex justify-center">{slides[currentSlide].icon}</div>
            <h1 className="text-5xl font-black italic mb-2 tracking-tighter">{slides[currentSlide].title}</h1>
            <p className="text-blue-400 font-bold mb-8 uppercase tracking-widest text-sm">{slides[currentSlide].subtitle}</p>
            {slides[currentSlide].content && <p className="text-slate-400 max-w-xl mx-auto text-lg mb-8">{slides[currentSlide].content}</p>}
            <div className="flex justify-center space-x-4 mt-8">
              <button onClick={prevSlide} className="p-2 bg-slate-900 rounded-full border border-slate-800"><ChevronLeft/></button>
              <div className="flex items-center space-x-2">{slides.map((_, i) => <div key={i} className={`h-1.5 rounded-full transition-all ${i === currentSlide ? 'w-6 bg-blue-500' : 'w-1.5 bg-slate-800'}`}/>)}</div>
              <button onClick={nextSlide} className="p-2 bg-slate-900 rounded-full border border-slate-800"><ChevronRight/></button>
            </div>
          </div>
        ) : <Prototype />}
      </main>
    </div>
  );
};

export default App;