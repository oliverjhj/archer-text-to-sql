import { useEffect, useState } from 'react';
import {
  InlineLoading,
  InlineNotification,
  Modal,
  Tag,
} from '@carbon/react';
import { apiUrl } from '../api/client';

interface SchemaColumn {
  name: string;
  type: string;
  common: boolean;
}

interface Schema {
  table: string;
  row_count: number;
  date_from: string | null;
  date_to: string | null;
  columns: SchemaColumn[];
  known_values: Record<string, string[]>;
}

interface SchemaPanelProps {
  open: boolean;
  onClose: () => void;
}

/**
 * A reference for what the dataset contains.
 *
 * Without this, a visitor is guessing at column names, and the questions
 * people invent while guessing are the ones that come back empty. The values
 * section exists for the same reason the prompt has one: someone who has to
 * guess whether a flag is 'Yes' or 'Y' will guess wrong, exactly as the model
 * did before it was told.
 */
export function SchemaPanel({ open, onClose }: SchemaPanelProps) {
  const [schema, setSchema] = useState<Schema | null>(null);
  const [failed, setFailed] = useState(false);

  // Fetched on first open rather than on mount: most visitors ask a question
  // without ever opening this, and there is no reason to spend a request on
  // them.
  useEffect(() => {
    if (!open || schema || failed) {
      return;
    }

    let cancelled = false;
    fetch(apiUrl('/api/schema'), { credentials: 'include' })
      .then((response) => {
        if (!response.ok) {
          throw new Error(String(response.status));
        }
        return response.json();
      })
      .then((body: Schema) => {
        if (!cancelled) setSchema(body);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });

    return () => {
      cancelled = true;
    };
  }, [open, schema, failed]);

  const common = schema?.columns.filter((column) => column.common) ?? [];
  const rest = schema?.columns.filter((column) => !column.common) ?? [];

  return (
    <Modal
      open={open}
      onRequestClose={onClose}
      modalHeading="Schema reference"
      modalLabel={schema ? schema.table : 'sales_data'}
      passiveModal
      size="md"
    >
      {!schema && !failed && <InlineLoading description="Loading schema..." status="active" />}

      {failed && (
        <InlineNotification
          kind="error"
          lowContrast
          hideCloseButton
          title="Could not load the schema"
          subtitle="You can still ask questions."
        />
      )}

      {schema && (
        <div className="archer-schema">
          <p className="archer-schema__summary">
            <strong>{schema.row_count.toLocaleString()}</strong> rows
            {schema.date_from && schema.date_to && (
              <>
                {' '}
                from <strong>{schema.date_from}</strong> to <strong>{schema.date_to}</strong>
              </>
            )}
            . Synthetic data.
          </p>

          <h4 className="archer-schema__heading">Most answers use these</h4>
          <div className="archer-schema__tags">
            {common.map((column) => (
              <Tag key={column.name} type="blue" size="sm">
                {column.name}
              </Tag>
            ))}
          </div>

          <h4 className="archer-schema__heading">Also available</h4>
          <div className="archer-schema__tags">
            {rest.map((column) => (
              <Tag key={column.name} type="cool-gray" size="sm">
                {column.name}
              </Tag>
            ))}
          </div>

          {Object.keys(schema.known_values).length > 0 && (
            <>
              <h4 className="archer-schema__heading">Fixed values</h4>
              <dl className="archer-schema__values">
                {Object.entries(schema.known_values).map(([column, values]) => (
                  <div key={column}>
                    <dt>{column}</dt>
                    <dd>{values.join(' · ')}</dd>
                  </div>
                ))}
              </dl>
            </>
          )}

          <p className="archer-schema__note">
            A "deal" is one document number and can span several rows, so counting
            deals is not the same as counting rows.
          </p>
        </div>
      )}
    </Modal>
  );
}
