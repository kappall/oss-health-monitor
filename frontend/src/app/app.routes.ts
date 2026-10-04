import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login';
import { CallbackComponent } from './features/auth/callback/callback';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    {
      path: '',
      redirectTo: 'dashboard',
      pathMatch: 'full'
    },
    {
      path: 'login',
      component: LoginComponent
    },
    {
      path: 'auth/callback',
      component: CallbackComponent
    },
    {
      path: 'dashboard',
      canActivate: [authGuard],
      loadComponent: () => import('./features/dashboard/dashboard').then(m => m.Dashboard)
    },
    {
      path: '**',
      redirectTo: 'dashboard'
    }
  ];
  