import {
  CodeSnippet,
  InlineLoading,
  InlineNotification,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tag,
} from '@carbon/react';
import { parseAnswer } from '../lib/answer';
import type { AnswerBlock } from '../lib/answer';
import type { ConversationEntry } from '../types/api';

interface AnswerItemProps {
  entry: ConversationEntry;
}

function renderBlock(block: AnswerBlock, key: number) {
  if (block.kind === 'table') {
    return (
      // Result tables can be far wider than the column, so they scroll
      // independently rather than forcing the page to scroll sideways.
      <div className="archer-answer__table" key={key}>
        <Table size="sm" useZebraStyles>
          <TableHead>
            <TableRow>
              {block.headers.map((header, index) => (
                <TableHeader key={`${key}-h-${index}`}>{header}</TableHeader>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {block.rows.map((row, rowIndex) => (
              <TableRow key={`${key}-r-${rowIndex}`}>
                {row.map((cell, cellIndex) => (
                  <TableCell key={`${key}-r-${rowIndex}-c-${cellIndex}`}>{cell}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  return (
    <p className="archer-answer__text" key={key}>
      {block.spans.map((span, index) =>
        span.bold ? (
          <strong key={`${key}-s-${index}`}>{span.text}</strong>
        ) : (
          <span key={`${key}-s-${index}`}>{span.text}</span>
        ),
      )}
    </p>
  );
}

/**
 * A single question/answer exchange, covering the loading, error, empty and
 * answered states.
 *
 * The answer is parsed into blocks and rendered as React elements. Nothing is
 * injected as HTML, so model output cannot become markup.
 */
export function AnswerItem({ entry }: AnswerItemProps) {
  const parsed = entry.answer ? parseAnswer(entry.answer) : null;

  return (
    <article className="archer-turn">
      <div className="archer-turn__question">
        <Tag type="cool-gray" size="sm">
          You
        </Tag>
        <p>{entry.question}</p>
      </div>
      <div className="archer-turn__answer">
        <Tag type="blue" size="sm">
          Archer
        </Tag>

        {entry.pending && (
          <InlineLoading description="Generating answer..." status="active" />
        )}

        {!entry.pending && entry.error && (
          <InlineNotification
            kind={entry.error.kind === 'unauthorised' ? 'warning' : 'error'}
            lowContrast
            hideCloseButton
            title={
              entry.error.kind === 'unauthorised'
                ? 'Session expired'
                : 'Something went wrong'
            }
            subtitle={entry.error.message}
          />
        )}

        {!entry.pending && !entry.error && parsed && (
          <>
            {parsed.blocks.map(renderBlock)}

            {parsed.note && (
              <p className="archer-answer__note">{parsed.note}</p>
            )}

            {parsed.sql && (
              // Showing the generated SQL is a deliberate transparency feature,
              // not debug output: the user can see exactly what ran.
              <div className="archer-answer__sql">
                <p className="archer-answer__sql-label">{parsed.sql.label}</p>
                <CodeSnippet type="multi" feedback="Copied" wrapText>
                  {parsed.sql.query}
                </CodeSnippet>
              </div>
            )}
          </>
        )}
      </div>
    </article>
  );
}
