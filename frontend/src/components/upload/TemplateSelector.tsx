import React from 'react'
import clsx from 'clsx'

export type TemplateType = 'abstract' | 'environment' | 'character' | 'minimal'

export interface TemplateSelectorProps {
  onSelect: (template: TemplateType) => void
  selectedTemplate?: TemplateType | null
  className?: string
  disabled?: boolean
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  onSelect,
  selectedTemplate,
  className,
  disabled = false,
}) => {
  const templates: { value: TemplateType; label: string }[] = [
    { value: 'abstract', label: 'Abstract' },
    { value: 'environment', label: 'Environment' },
    { value: 'character', label: 'Character' },
    { value: 'minimal', label: 'Minimal' },
  ]

  return (
    <div className={clsx('flex items-center gap-1', className)}>
      {templates.map((template) => {
        const isSelected = selectedTemplate === template.value
        return (
          <button
            key={template.value}
            onClick={() => !disabled && onSelect(template.value)}
            disabled={disabled}
            className={clsx(
              'px-2 py-1 text-xs font-medium rounded transition-colors',
              'border border-vc-border',
              disabled
                ? isSelected
                  ? 'opacity-60 cursor-not-allowed bg-vc-accent-primary/20 text-vc-accent-primary border-vc-accent-primary'
                  : 'opacity-50 cursor-not-allowed bg-vc-surface-primary text-vc-text-muted'
                : isSelected
                  ? 'bg-vc-accent-primary/20 text-vc-accent-primary border-vc-accent-primary'
                  : 'bg-vc-surface-primary text-vc-text-secondary hover:bg-vc-surface-primary/80 hover:text-vc-text-primary',
            )}
          >
            {template.label}
          </button>
        )
      })}
    </div>
  )
}
