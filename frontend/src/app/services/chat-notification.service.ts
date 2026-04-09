import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject } from 'rxjs';

const API = 'http://localhost:8001';

@Injectable({ providedIn: 'root' })
export class ChatNotificationService implements OnDestroy {
  private _unread = new BehaviorSubject<number>(0);
  unread$ = this._unread.asObservable();

  private _unreadRooms = new BehaviorSubject<Set<string>>(new Set());
  unreadRooms$ = this._unreadRooms.asObservable();

  private interval: any;
  // room_id -> last seen timestamp
  private lastSeenTs: Record<string, string> = {};

  constructor(private http: HttpClient) {}

  startPolling() {
    if (this.interval) return;
    this.poll();
    this.interval = setInterval(() => this.poll(), 5000);
  }

  stopPolling() {
    clearInterval(this.interval);
    this.interval = null;
  }

  markRoomRead(roomId: string) {
    // Record current time as last seen for this room
    this.lastSeenTs[roomId] = new Date().toISOString();
    const current = new Set(this._unreadRooms.value);
    current.delete(roomId);
    this._unreadRooms.next(current);
    this._unread.next(current.size);
  }

  isRoomUnread(roomId: string): boolean {
    return this._unreadRooms.value.has(roomId);
  }

  private poll() {
    const token = this.getToken();
    if (!token) return;
    this.http.get<any[]>(`${API}/manager-chat/rooms?token=${token}`).subscribe({
      next: (rooms) => {
        const unreadRooms = new Set(this._unreadRooms.value);
        for (const r of rooms) {
          if (!r.last_ts || r.last_role !== 'user') continue;
          const seen = this.lastSeenTs[r.room_id];
          if (!seen || r.last_ts > seen) {
            unreadRooms.add(r.room_id);
          }
        }
        this._unreadRooms.next(unreadRooms);
        this._unread.next(unreadRooms.size);
      },
      error: () => {}
    });
  }

  private getToken(): string {
    return localStorage.getItem('cat_token') || '';
  }

  ngOnDestroy() { this.stopPolling(); }
}
