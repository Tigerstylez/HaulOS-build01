import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  ViewStyle,
} from 'react-native';

import { theme } from '../theme';

export function Screen({ children }: { children: React.ReactNode }) {
  return <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent}>{children}</ScrollView>;
}

export function Card({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <View style={{ marginBottom: theme.spacing.sm }}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  );
}

export function Label({ text }: { text: string }) {
  return <Text style={styles.label}>{text}</Text>;
}

export function TextField({ value, onChangeText, placeholder, keyboardType = 'default', multiline = false }: {
  value: string;
  onChangeText: (next: string) => void;
  placeholder?: string;
  keyboardType?: 'default' | 'numeric' | 'number-pad';
  multiline?: boolean;
}) {
  return (
    <TextInput
      style={[styles.input, multiline ? styles.multiline : null]}
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor={theme.colors.textMuted}
      keyboardType={keyboardType}
      multiline={multiline}
    />
  );
}

export function PrimaryButton({ title, onPress, disabled = false }: { title: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable disabled={disabled} onPress={onPress} style={[styles.button, styles.buttonPrimary, disabled ? styles.disabled : null]}>
      <Text style={styles.buttonText}>{title}</Text>
    </Pressable>
  );
}

export function SecondaryButton({ title, onPress }: { title: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.button, styles.buttonSecondary]}>
      <Text style={styles.buttonText}>{title}</Text>
    </Pressable>
  );
}

export function Chip({ title, selected, onPress }: { title: string; selected: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, selected ? styles.chipSelected : null]}>
      <Text style={styles.chipText}>{title}</Text>
    </Pressable>
  );
}

export function StatusPill({ text, tone = 'neutral' }: { text: string; tone?: 'neutral' | 'success' | 'warning' | 'danger' }) {
  const toneStyle = tone === 'success' ? styles.pillSuccess : tone === 'warning' ? styles.pillWarning : tone === 'danger' ? styles.pillDanger : styles.pillNeutral;
  return (
    <View style={[styles.pill, toneStyle]}>
      <Text style={styles.pillText}>{text}</Text>
    </View>
  );
}

export function KVRow({ label, value }: { label: string; value: string | number | undefined | null }) {
  return (
    <View style={styles.kvRow}>
      <Text style={styles.kvLabel}>{label}</Text>
      <Text style={styles.kvValue}>{value ?? '—'}</Text>
    </View>
  );
}

export function Divider() {
  return <View style={styles.divider} />;
}

export function MapPlaceholder({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <View style={styles.mapPlaceholder}>
      <Text style={styles.mapTitle}>{title}</Text>
      {subtitle ? <Text style={styles.mapSubtitle}>{subtitle}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.colors.bg,
  },
  screenContent: {
    padding: theme.spacing.md,
    gap: theme.spacing.md,
  },
  card: {
    backgroundColor: theme.colors.card,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  sectionTitle: {
    color: theme.colors.text,
    fontSize: 20,
    fontWeight: '700',
  },
  subtitle: {
    color: theme.colors.textMuted,
    marginTop: 4,
  },
  label: {
    color: theme.colors.textMuted,
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.cardAlt,
    borderRadius: theme.radius.md,
    color: theme.colors.text,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  multiline: {
    minHeight: 90,
    textAlignVertical: 'top',
  },
  button: {
    borderRadius: theme.radius.md,
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonPrimary: {
    backgroundColor: theme.colors.primary,
  },
  buttonSecondary: {
    backgroundColor: theme.colors.cardAlt,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  disabled: {
    opacity: 0.45,
  },
  buttonText: {
    color: theme.colors.text,
    fontWeight: '700',
  },
  chip: {
    backgroundColor: theme.colors.chip,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.colors.border,
    marginRight: 8,
    marginBottom: 8,
  },
  chipSelected: {
    borderColor: theme.colors.primary,
    backgroundColor: '#143350',
  },
  chipText: {
    color: theme.colors.text,
    fontWeight: '600',
  },
  pill: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  pillText: {
    color: theme.colors.text,
    fontWeight: '700',
    fontSize: 12,
    textTransform: 'uppercase',
  },
  pillNeutral: {
    backgroundColor: theme.colors.cardAlt,
  },
  pillSuccess: {
    backgroundColor: '#164533',
  },
  pillWarning: {
    backgroundColor: '#5A3A10',
  },
  pillDanger: {
    backgroundColor: '#5A1F25',
  },
  kvRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  kvLabel: {
    color: theme.colors.textMuted,
    flex: 1,
  },
  kvValue: {
    color: theme.colors.text,
    flex: 1,
    textAlign: 'right',
    fontWeight: '600',
  },
  divider: {
    height: 1,
    backgroundColor: theme.colors.border,
  },
  mapPlaceholder: {
    minHeight: 180,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: theme.colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0B1624',
    padding: theme.spacing.md,
  },
  mapTitle: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
  },
  mapSubtitle: {
    color: theme.colors.textMuted,
    marginTop: 8,
    textAlign: 'center',
  },
});
