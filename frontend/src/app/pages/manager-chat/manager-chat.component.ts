import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ChatNotificationService } from '../../services/chat-notification.service';

const API = 'http://localhost:8001';
const WS_BASE = 'ws://localhost:8001';

interface Message { role: string; content: string; sender: string; ts: string; }
interface Room { room_id: string; user_name: string; last_message: string; last_ts: string; online: boolean; }

@Component({
  selector: 'app-manager-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './manager-chat.component.html',
  styleUrl: './manager-chat.component.scss',
})
export class ManagerChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;

  rooms: Room[] = [];
  selectedRoom = '';
  selectedRoomName = '';
  messages: Message[] = [];
  input = '';
  connected = false;
  statusText = '';
  private ws: WebSocket | null = null;
  private managerName = '';
  private shouldScroll = false;

  constructor(private http: HttpClient, public notify: ChatNotificationService) {}

  ngOnInit() {
    this.managerName = localStorage.getItem('cat_name') || 'Manager';
    this.loadRooms();
    setInterval(() => this.loadRooms(), 5000);
  }

  ngOnDestroy() { this.ws?.close(); }

  ngAfterViewChecked() {
    if (this.shouldScroll) { this.scrollToBottom(); this.shouldScroll = false; }
  }

  loadRooms() {
    const token = localStorage.getItem('cat_token') || '';
    this.http.get<Room[]>(`${API}/manager-chat/rooms?token=${token}`).subscribe({
      next: (r) => this.rooms = r,
      error: () => {}
    });
  }

  selectRoom(roomId: string) {
    if (this.selectedRoom === roomId) return;
    this.ws?.close();
    this.selectedRoom = roomId;
    this.selectedRoomName = this.rooms.find(r => r.room_id === roomId)?.user_name || roomId;
    this.messages = [];
    this.notify.markRoomRead(roomId);
    this.statusText = 'Connecting...';
    const url = `${WS_BASE}/ws/manager-chat/${roomId}?role=manager&name=${encodeURIComponent(this.managerName)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => { this.connected = true; this.statusText = 'Connected'; };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'history') {
        this.messages = data.messages || [];
      } else if (data.type === 'message') {
        this.messages.push({ role: data.role, content: data.content, sender: data.sender, ts: data.ts });
      } else if (data.type === 'status') {
        this.statusText = data.content;
      }
      this.shouldScroll = true;
    };

    this.ws.onclose = () => { this.connected = false; this.statusText = 'Disconnected'; };
  }

  send() {
    const text = this.input.trim();
    if (!text || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    this.ws.send(text);
    this.input = '';
    // Don't push locally — backend broadcasts it back
  }

  onKeydown(e: KeyboardEvent) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.send(); } }

  private scrollToBottom() {
    try { this.messagesEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' }); } catch {}
  }
}
