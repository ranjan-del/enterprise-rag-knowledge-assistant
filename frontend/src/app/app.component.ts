import { Component } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';

// Root shell. TODO: add nav layout guarded by auth state (MEMORY.md Dashboard).
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink],
  templateUrl: './app.component.html',
})
export class AppComponent {
  title = 'Enterprise RAG Knowledge Assistant';
}
