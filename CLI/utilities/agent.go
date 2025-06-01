package utilities

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

var baseUrl = "https://gerardosanchezz--codemedic-server-fastapi-app.modal.run/"

func sendRequest(method, url string, body io.Reader) (*http.Response, error) {
	req, err := http.NewRequest(method, url, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	httpClient := &http.Client{}
	response, err := httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to perform request: %w", err)
	}
	return response, err
}

func FixIssue(request FixCodeRequest) (AgentResponse, error) {
	jsonBody, err := json.Marshal(request)
	if err != nil {
		return AgentResponse{}, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := sendRequest(http.MethodPost, baseUrl, bytes.NewBuffer(jsonBody))
	if err != nil {
		return AgentResponse{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return AgentResponse{}, fmt.Errorf("API error (%d): %s", resp.StatusCode, string(bodyBytes))
	}

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return AgentResponse{}, fmt.Errorf("failed to read response body: %w", err)
	}

	var agentResponse AgentResponse
	err = json.Unmarshal(bodyBytes, &agentResponse)
	if err != nil {
		return AgentResponse{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return agentResponse, nil
}
