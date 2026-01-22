// Locale files index
// Import all locale files here
import en from './en';
import zhCN from './zh-CN';
import zhHK from './zh-HK';
import ja from './ja';
import kr from './kr';
import fr from './fr';
import ar from './ar';
import ru from './ru';
import es from './es';

// Export type for locale keys
export type Locale = 'en' | 'zh-CN' | 'zh-HK' | 'ja' | 'kr' | 'fr' | 'ar' | 'ru' | 'es';

// Export translations map
export const translations: Record<Locale, Record<string, string>> = {
  'en': en,
  'zh-CN': zhCN,
  'zh-HK': zhHK,
  'ja': ja,
  'kr': kr,
  'fr': fr,
  'ar': ar,
  'ru': ru,
  'es': es,
};

// Export available locales
export const availableLocales: Locale[] = ['en', 'zh-CN', 'zh-HK', 'ja', 'kr', 'fr', 'ar', 'ru', 'es'];

// Export locale display names
export const localeNames: Record<Locale, string> = {
  'en': 'English',
  'zh-CN': '简体中文',
  'zh-HK': '繁體中文',
  'ja': '日本語',
  'kr': '한국어',
  'fr': 'Français',
  'ar': 'العربية',
  'ru': 'Русский',
  'es': 'Español',
};
