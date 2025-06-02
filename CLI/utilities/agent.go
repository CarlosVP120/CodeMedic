package utilities

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// API endpoint URL
// var baseUrl = "https://gerardosanchezz--codemedic-server-fastapi-app.modal.run/"
//var baseUrl = "http://localhost:8000/api/fix/"

var baseUrl = "https://codemedic-203855113547.us-central1.run.app/api/fix/"

func sendRequest(method, url string, body io.Reader) (*http.Response, []byte, error) {
	fmt.Println("🚀 Starting request to URL:", url)

	// Store the body bytes for retries
	bodyBytes, err := io.ReadAll(body)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read request body: %w", err)
	}

	// Create the HTTP client with 10-minute timeout
	httpClient := &http.Client{
		Timeout: 600 * time.Second, // 10 minutes
		Transport: &http.Transport{
			MaxIdleConns:        10,
			IdleConnTimeout:     600 * time.Second, // Also increased idle timeout
			DisableCompression:  false,
			DisableKeepAlives:   false,
			MaxIdleConnsPerHost: 10,
		},
	}

	// Create new request
	req, err := http.NewRequest(method, url, bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Accept", "application/json")

	fmt.Println("📡 Sending request with 10-minute timeout...")

	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to perform request: %w", err)
	}

	defer resp.Body.Close()
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return resp, nil, fmt.Errorf("failed to read response body: %w", err)
	}

	return resp, respBody, nil
}

func FixIssue(request FixCodeRequest) (AgentResponse, error) {
	fmt.Println("🔧 Starting FixIssue function")
	fmt.Printf("📋 Processing issue #%d: %s\n", request.GithubIssueData.Number, request.GithubIssueData.Title)
	jsonBody, err := json.Marshal(request)
	if err != nil {
		fmt.Println("❌ Error marshaling request:", err)
		return AgentResponse{}, fmt.Errorf("failed to marshal request: %w", err)
	}
	fmt.Printf("📦 Request JSON prepared, size: %d bytes\n", len(jsonBody))

	fmt.Printf("📤 Sending request to %s\n", baseUrl)
	resp, bodyBytes, err := sendRequest(http.MethodPost, baseUrl, bytes.NewBuffer(jsonBody))
	if err != nil {
		fmt.Println("❌ Error from sendRequest:", err)
		return AgentResponse{}, err
	}

	fmt.Printf("📥 Response received with status: %d %s\n", resp.StatusCode, resp.Status)
	if resp.StatusCode != http.StatusOK {
		fmt.Printf("⚠️ API returned non-200 status: %d %s\n", resp.StatusCode, resp.Status)
		fmt.Printf("⚠️ Error response body: %s\n", string(bodyBytes))
		return AgentResponse{}, fmt.Errorf("API error (%d): %s", resp.StatusCode, string(bodyBytes))
	}

	fmt.Println("🔄 Unmarshaling response to AgentResponse structure...")
	var agentResponse AgentResponse
	err = json.Unmarshal(bodyBytes, &agentResponse)
	if err != nil {
		fmt.Println("❌ Error unmarshaling response:", err)
		fmt.Printf("📄 Raw response: %s\n", string(bodyBytes))
		return AgentResponse{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	fmt.Println("✅ Successfully unmarshaled response")

	return agentResponse, nil
}
