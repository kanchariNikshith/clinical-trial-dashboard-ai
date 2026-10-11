export * from './health';

export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: string;
  badge?: string;
  phase: number;
}
