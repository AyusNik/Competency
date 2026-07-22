import { Component } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';
import { ChatbotComponent } from './components/chatbot/chatbot.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ChatbotComponent],
  templateUrl: './app.component.html',
})
export class AppComponent {
  showChatbot = false;

  constructor(private router: Router) {
    this.showChatbot = !this.router.url.startsWith('/login');
    this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe((event) => {
        const nav = event as NavigationEnd;
        this.showChatbot = !nav.urlAfterRedirects.startsWith('/login');
      });
  }
}
