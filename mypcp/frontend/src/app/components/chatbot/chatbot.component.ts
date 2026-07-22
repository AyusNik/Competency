import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

const API = 'http://localhost:8001';
const WS_BASE = 'ws://localhost:8001';

const MANAGER_TRIGGERS = [
  'talk to manager', 'speak to manager', 'connect manager', 'contact manager',
  'reach manager', 'chat with manager', 'message manager', 'call manager',
  'i want manager', 'need manager', 'manager please', 'live chat',
  'talk to my manager', 'speak to my manager', 'connect to manager',
  'connect to my manager', 'chat with my manager', 'contact my manager',
  'reach my manager', 'message my manager', 'talk with manager', 'talk with my manager'
];

export interface Message {
  role: 'user' | 'assistant' | 'manager' | 'system';
  content: string;
  sender?: string;
}

declare var webkitSpeechRecognition: any;
declare var SpeechRecognition: any;

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrl: './chatbot.component.scss',
})
export class ChatbotComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;

  open = false;
  messages: Message[] = [];
  input = '';
  loading = false;
  recording = false;
  micSupported = false;
  private recognition: any = null;

  // Manager live chat state
  managerMode = false;
  managerConnected = false;
  showConnectPrompt = false;
  private ws: WebSocket | null = null;
  private roomId = '';
  private userName = '';
  private shouldScroll = false;
  private certStep1Path = '/chat/cert-step-2.jpg';
  private certStep2Path = '/chat/cert-step-1.png';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.userName = localStorage.getItem('user_name') || 'User';
    this.roomId = this.parseUserId() || 'room_' + Date.now();
    this.micSupported = !!(typeof SpeechRecognition !== 'undefined' || typeof webkitSpeechRecognition !== 'undefined');
    this.http.delete(`${API}/chat/history`).subscribe({ error: () => {} });
    const prefill = localStorage.getItem('chatbot_prefill');
    if (prefill) {
      this.open = true;
      this.input = prefill;
      localStorage.removeItem('chatbot_prefill');
    }
  }

  ngOnDestroy() {
    this.ws?.close();
    this.recognition?.stop();
  }

  ngAfterViewChecked() {
    if (this.shouldScroll) { this.scrollToBottom(); this.shouldScroll = false; }
  }

  private parseUserId(): string {
    try {
      const token = localStorage.getItem('token');
      if (!token) return '';
      return JSON.parse(atob(token.split('.')[1]))?.sub || '';
    } catch { return ''; }
  }

  toggle() {
    this.open = !this.open;
    if (this.open) {
      this.shouldScroll = true;
      const prefill = localStorage.getItem('chatbot_prefill');
      if (prefill) {
        this.input = prefill;
        localStorage.removeItem('chatbot_prefill');
      }
    }
  }

  toggleMic() {
    if (!this.micSupported) return;
    if (this.recording) {
      this.recognition?.stop();
      return;
    }
    const SR = typeof SpeechRecognition !== 'undefined' ? SpeechRecognition : webkitSpeechRecognition;
    this.recognition = new SR();
    this.recognition.lang = 'en-US';
    this.recognition.interimResults = true;
    this.recognition.continuous = false;

    let finalTranscript = '';
    this.recording = true;

    this.recognition.onresult = (event: any) => {
      let interim = '';
      finalTranscript = '';
      for (let i = 0; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        event.results[i].isFinal ? finalTranscript += t : interim += t;
      }
      this.input = finalTranscript || interim;
    };

    this.recognition.onend = () => {
      this.recording = false;
    };

    this.recognition.onerror = (e: any) => {
      this.recording = false;
      if (e.error === 'not-allowed')
        this.messages.push({ role: 'system', content: 'Microphone access denied. Please allow mic permission in your browser.' });
    };

    this.recognition.start();
  }

  send() {
    const text = this.input.trim();
    if (!text || this.loading) return;
    this.input = '';

    if (this.managerMode) {
      if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(text);
      return;
    }

    this.messages.push({ role: 'user', content: text });
    this.shouldScroll = true;

    if (MANAGER_TRIGGERS.some(t => text.toLowerCase().includes(t))) {
      this.messages.push({ role: 'assistant', content: `Connecting you with your Business Line Manager now...` });
      this.shouldScroll = true;
      this.connectToManager();
      return;
    }

    this.loading = true;
    this.http.post<any>(`${API}/chat/`, { message: text }).subscribe({
      next: (res) => {
        this.messages.push({ role: 'assistant', content: res.reply });
        this.loading = false;
        this.shouldScroll = true;
        if (res.reply?.toLowerCase().includes('manager') && res.reply?.toLowerCase().includes('contact')) {
          this.showConnectPrompt = true;
        }
      },
      error: () => {
        this.messages.push({ role: 'assistant', content: 'Sorry, something went wrong. Please try again.' });
        this.loading = false;
        this.shouldScroll = true;
      },
    });
  }

  connectToManager() {
    this.showConnectPrompt = false;
    this.managerMode = true;
    this.messages.push({ role: 'system', content: 'Connecting to your Business Line Manager...' });
    this.shouldScroll = true;

    const url = `${WS_BASE}/ws/manager-chat/${this.roomId}?role=user&name=${encodeURIComponent(this.userName)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.managerConnected = true;
      this.messages.push({ role: 'system', content: '✅ Connected to your manager. You can now chat directly.' });
      this.shouldScroll = true;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'history') {
        const prev = (data.messages || []).filter((m: any) => m.role === 'manager');
        prev.forEach((m: any) => this.messages.push({ role: 'manager', content: m.content, sender: m.sender }));
      } else if (data.type === 'message') {
        if (data.role === 'manager') this.messages.push({ role: 'manager', content: data.content, sender: data.sender });
        else if (data.role === 'user') this.messages.push({ role: 'user', content: data.content });
      } else if (data.type === 'status') {
        this.messages.push({ role: 'system', content: data.content });
        if (data.content?.includes('Manager has left. Chat ended.')) {
          this.shouldScroll = true;
          setTimeout(() => this._resetAfterChat(), 1500);
        }
      }
      this.shouldScroll = true;
    };

    this.ws.onclose = () => { this.managerConnected = false; this._resetAfterChat(); };
  }

  disconnectManager() { this.ws?.close(); }

  private _resetAfterChat() {
    this.ws?.close();
    this.ws = null;
    this.managerMode = false;
    this.managerConnected = false;
    this.messages = [];
    this.http.delete(`${API}/chat/history`).subscribe({ error: () => {} });
  }

  clearChat() {
    this.http.delete(`${API}/chat/history`).subscribe();
    this.messages = [];
    this.managerMode = false;
    this.ws?.close();
  }

  onKeydown(e: KeyboardEvent) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.send(); } }

  formatAssistantMessage(content: string): string {
    const escaped = this.escapeHtml(content || '');
    const withBreaks = escaped.replace(/\n/g, '<br>');
    return withBreaks
      .replace(/\[\[CERT_STEP_1\]\]/g, this.stepImageHtml(1))
      .replace(/\[\[CERT_STEP_2\]\]/g, this.stepImageHtml(2));
  }

  private stepImageHtml(step: 1 | 2): string {
    const src = step === 1 ? this.certStep1Path : this.certStep2Path;
    const caption = step === 1 ? 'Open ESM and use Manage MyPCP Certifications catalog.' : 'Select your action and submit ticket to GBS-HSE-MYPCP-L1.';
    return `<div class="cert-step"><div class="cert-step-title">Step ${step}</div><img src="${src}" alt="Certification step ${step}" class="cert-step-img" /><div class="cert-step-caption">${caption}</div></div>`;
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  private scrollToBottom() {
    try { this.messagesEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' }); } catch {}
  }
}
