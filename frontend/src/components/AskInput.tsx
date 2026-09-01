import { useState } from 'react';
import type { ChangeEvent, FormEvent, KeyboardEvent } from 'react';
import { Button, TextArea } from '@carbon/react';
import { Send } from '@carbon/icons-react';

interface AskInputProps {
  busy: boolean;
  onSubmit: (question: string) => void;
}

// Natural-language question input. Enter submits; Shift+Enter inserts a newline.
export function AskInput({ busy, onSubmit }: AskInputProps) {
  const [value, setValue] = useState('');

  const canSubmit = value.trim().length > 0 && !busy;

  const send = () => {
    if (!canSubmit) {
      return;
    }
    onSubmit(value.trim());
    setValue('');
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    send();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  };

  return (
    <form className="archer-ask" onSubmit={handleSubmit}>
      <TextArea
        id="archer-question"
        labelText="Ask a question about the data"
        placeholder="e.g. What was the total revenue last quarter?"
        rows={2}
        value={value}
        disabled={busy}
        onChange={(event: ChangeEvent<HTMLTextAreaElement>) =>
          setValue(event.target.value)
        }
        onKeyDown={handleKeyDown}
      />
      <div className="archer-ask__actions">
        <Button type="submit" renderIcon={Send} disabled={!canSubmit}>
          Ask
        </Button>
      </div>
    </form>
  );
}
