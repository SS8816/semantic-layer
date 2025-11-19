import React, { useState, useEffect } from 'react';
import { Modal } from './ui';
import MetadataViewer from './MetadataViewer';

const MetadataEditModal = ({ isOpen, onClose, table }) => {
  if (!table) return null;

  // Construct table name from catalog.schema.table_name
  const tableName = table.full_name;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Edit Metadata: ${table.table_name}`} size="full">
      <MetadataViewer tableName={tableName} />
    </Modal>
  );
};

export default MetadataEditModal;
