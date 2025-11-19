/**
 * AliasEditor Component
 * Inline editor for column aliases
 */
import React, { useState } from 'react';
import './AliasEditor.css';

const AliasEditor = ({ aliases, onSave, onCancel }) => {
  const [editedAliases, setEditedAliases] = useState([...aliases]);
  const [newAlias, setNewAlias] = useState('');

  const handleAddAlias = () => {
    if (newAlias.trim()) {
      setEditedAliases([...editedAliases, newAlias.trim()]);
      setNewAlias('');
    }
  };

  const handleRemoveAlias = (index) => {
    setEditedAliases(editedAliases.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    if (editedAliases.length === 0) {
      alert('Please add at least one alias');
      return;
    }
    onSave(editedAliases);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddAlias();
    }
  };

  return (
    <div className="alias-editor">
      <div className="alias-list">
        {editedAliases.map((alias, index) => (
          <div key={index} className="alias-item">
            <span>{alias}</span>
            <button
              onClick={() => handleRemoveAlias(index)}
              className="remove-alias-button"
              title="Remove alias"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="add-alias-row">
        <input
          type="text"
          value={newAlias}
          onChange={(e) => setNewAlias(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Add new alias..."
          className="alias-input"
        />
        <button onClick={handleAddAlias} className="add-alias-button">
          Add
        </button>
      </div>

      <div className="editor-actions">
        <button onClick={handleSave} className="save-button">
          Save
        </button>
        <button onClick={onCancel} className="cancel-button">
          Cancel
        </button>
      </div>
    </div>
  );
};

export default AliasEditor;