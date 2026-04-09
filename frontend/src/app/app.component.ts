import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar.component';
import { ManagerChatBubbleComponent } from './components/manager-chat-bubble/manager-chat-bubble.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NavbarComponent, ManagerChatBubbleComponent],
  template: `
    <app-navbar />
    <router-outlet />
    <app-manager-chat-bubble />
  `,
})
export class AppComponent {}
