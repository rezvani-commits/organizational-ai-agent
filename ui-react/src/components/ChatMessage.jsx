

import { BrandIcon } from "./icons";

export function UserMessage({ message }) {
  return (
    <div className="user-message-row">
      <div className="user-message">{message}</div>
    </div>
  );
}

export function AIMessage({ answer }) {
  return (
    <div className="ai-message-row">
      <div className="ai-message">
        <div className="ai-title">
          <span className="ai-icon">
            <BrandIcon size={16} />
          </span>
          <span>نیرویار</span>
        </div>
        <div className="ai-content">{answer}</div>
      </div>
    </div>
  );
}
