import { registerRootComponent } from 'expo';

import App from './App';

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);

// PWA: only meaningful on web, and only in a production build. Guarding here
// keeps navigator.serviceWorker out of the native Android/iOS bundles entirely.
import { registerServiceWorker } from './src/utils/pwa';
registerServiceWorker();
