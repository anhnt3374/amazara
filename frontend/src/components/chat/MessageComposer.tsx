import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import clsx from 'clsx'

interface Props {
  disabled?: boolean
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  onSend: (content: string) => Promise<void> | void
}

export default function MessageComposer({
  disabled,
  placeholder = 'Type a message...',
  value,
  onChange,
  onSend,
}: Props) {
  const [internalValue, setInternalValue] = useState('')
  const [sending, setSending] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const currentValue = value ?? internalValue

  useEffect(() => {
    if (value === undefined || !textareaRef.current) return
    textareaRef.current.focus()
    const caret = value.length
    textareaRef.current.setSelectionRange(caret, caret)
  }, [value])

  const setValue = (next: string) => {
    if (onChange) {
      onChange(next)
      return
    }
    setInternalValue(next)
  }

  const submit = async (e?: FormEvent) => {
    if (e) e.preventDefault()
    const content = currentValue.trim()
    if (!content || sending) return
    setSending(true)
    try {
      await onSend(content)
      setValue('')
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void submit()
    }
  }

  return (
    <form
      onSubmit={submit}
      className="flex items-end gap-2 border-t border-sand bg-white px-4 py-3"
    >
      <textarea
        ref={textareaRef}
        value={currentValue}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 resize-none max-h-32 rounded-pin border border-sand bg-fog px-3 py-2 text-sm text-plum placeholder:text-warm-silver focus:outline-none focus:border-[color:var(--color-border-hover)]"
      />
      <button
        type="submit"
        disabled={disabled || sending || !currentValue.trim()}
        className={clsx(
          'h-10 px-4 rounded-pin text-sm font-semibold transition-colors',
          disabled || !currentValue.trim()
            ? 'bg-sand text-warm-silver cursor-not-allowed'
            : 'bg-brand-red text-white hover:bg-[var(--color-brand-red-hover)]',
        )}
      >
        Send
      </button>
    </form>
  )
}
