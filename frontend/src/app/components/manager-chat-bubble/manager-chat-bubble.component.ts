import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';

const API = 'http://localhost:8001';
const WS_BASE = 'ws://localhost:8001';

interface Room { room_id: string; user_name: string; last_message: string; last_ts: string; online: boolean; }
interface Message { role: string; content: string; sender: string; ts: string; }

@Component({
  selector: 'app-manager-chat-bubble',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './manager-chat-bubble.component.html',
  styleUrl: './manager-chat-bubble.component.scss',
})
export class ManagerChatBubbleComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;

  open = false;
  rooms: Room[] = [];
  activeRoom: Room | null = null;
  messages: Message[] = [];
  input = '';
  connected = false;
  statusText = '';
  unreadCount = 0;

  private ws: WebSocket | null = null;
  private managerName = '';
  private pollInterval: any;
  private shouldScroll = false;
  private managerLeft = false;

  constructor(private http: HttpClient, public auth: AuthService) {}

  ngOnInit() {
    this.managerName = localStorage.getItem('cat_name') || 'Manager';
    this.loadRooms();
    this.pollInterval = setInterval(() => this.loadRooms(), 5000);
  }

  ngOnDestroy() {
    clearInterval(this.pollInterval);
    this._leaveRoom(false);
  }

  ngAfterViewChecked() {
    if (this.shouldScroll) { this.scrollToBottom(); this.shouldScroll = false; }
  }

  toggle() {
    this.open = !this.open;
    if (this.open) { this.unreadCount = 0; this.loadRooms(); }
  }

  loadRooms() {
    const token = localStorage.getItem('cat_token') || '';
    if (!token) return;
    this.http.get<Room[]>(`${API}/manager-chat/rooms?token=${token}`).subscribe({
      next: (r) => {
        const prevCount = this.rooms.length;
        this.rooms = r;
        if (!this.open && r.length > prevCount) this.unreadCount = r.length - prevCount;
      },
      error: () => {}
    });
  }

  joinRoom(room: Room) {
    if (this.activeRoom?.room_id === room.room_id) return;
    this._leaveRoom(false);
    this.activeRoom = room;
    this.messages = [];
    this.statusText = 'Connecting...';
    this.connected = false;

    const url = `${WS_BASE}/ws/manager-chat/${room.room_id}?role=manager&name=${encodeURIComponent(this.managerName)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => { this.connected = true; this.statusText = 'Connected'; };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'history') {
        this.messages = data.messages || [];
      } else if (data.type === 'message') {
        this.messages.push({ role: data.role, content: data.content, sender: data.sender, ts: data.ts });
      } else if (data.type === 'status') {
        this.messages.push({ role: 'status', content: data.content, sender: '', ts: '' });
        // User disconnected — backend notified us, reset back to room list
        if (data.content?.includes('has left. Chat ended.')) {
          this.shouldScroll = true;
          setTimeout(() => {
            this.managerLeft = true;
            this.ws?.close();
            this.ws = null;
            this.activeRoom = null;
            this.messages = [];
            this.connected = false;
            this.loadRooms();
          }, 1500);
        }
      }
      this.shouldScroll = true;
    };

    this.ws.onclose = () => {
      this.connected = false;
      // If manager didn't initiate the close, user disconnected — go back to room list
      if (!this.managerLeft) {
        this.activeRoom = null;
        this.messages = [];
        this.ws = null;
        this.loadRooms();
      }
      this.managerLeft = false;
    };
  }

  leaveRoom() {
    this._leaveRoom(true);
  }

  private _leaveRoom(deleteRoom: boolean) {
    if (!this.activeRoom) return;
    const roomId = this.activeRoom.room_id;
    this.managerLeft = true;
    this.ws?.close();
    this.ws = null;
    this.activeRoom = null;
    this.messages = [];
    this.connected = false;
    if (deleteRoom) {
      this.http.delete(`${API}/manager-chat/room/${roomId}`).subscribe({ error: () => {} });
      this.rooms = this.rooms.filter(r => r.room_id !== roomId);
    }
  }

  send() {
    const text = this.input.trim();
    if (!text || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    this.ws.send(text);
    this.input = '';
  }

  onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.send(); }
  }

  private scrollToBottom() {
    try { this.messagesEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' }); } catch {}
  }
}
