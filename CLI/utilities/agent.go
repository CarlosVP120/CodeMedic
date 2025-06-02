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

	// Store body in memory for reuse
	bodyBytes, err := io.ReadAll(body)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read request body: %w", err)
	}

	// HTTP transport setup
	transport := &http.Transport{
		MaxIdleConns:      0, // no idle conn reuse
		IdleConnTimeout:   30 * time.Second,
		DisableKeepAlives: true,
		ForceAttemptHTTP2: false, // optional: try disabling HTTP/2
	}
	client := &http.Client{
		Timeout:   120 * time.Second,
		Transport: transport,
	}

	// Build request
	req, err := http.NewRequest(method, url, io.NopCloser(bytes.NewReader(bodyBytes)))
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	fmt.Println("📡 Sending request...")

	// Make request
	resp, err := client.Do(req)
	if err != nil {
		if err.Error() == "unexpected EOF" {
			return nil, nil, fmt.Errorf("server closed connection unexpectedly (possible crash or content-length issue): %w", err)
		}
		return nil, nil, fmt.Errorf("failed to perform request: %w", err)
	}

	if resp == nil {
		return nil, nil, fmt.Errorf("received nil response")
	}
	defer resp.Body.Close()

	// Read response
	var buffer bytes.Buffer
	bytesRead, err := io.Copy(&buffer, resp.Body)
	if err != nil {
		return resp, nil, fmt.Errorf("error reading response body: %w", err)
	}

	// Check content length
	if resp.ContentLength > 0 && bytesRead != resp.ContentLength {
		fmt.Printf("⚠️ Content length mismatch: expected %d bytes, got %d\n", resp.ContentLength, bytesRead)
	}

	return resp, buffer.Bytes(), nil
}

func FixIssue(request FixCodeRequest) (AgentResponse, error) {
	fmt.Println("🔧 Starting FixIssue function")
	fmt.Printf("📋 Processing issue #%d: %s\n", request.GithubIssueData.Number, request.GithubIssueData.Title)

	jsonBody, err := json.Marshal(request)
	if err != nil {
		return AgentResponse{}, fmt.Errorf("failed to marshal request: %w", err)
	}
	fmt.Printf("📦 Request JSON prepared, size: %d bytes\n", len(jsonBody))

	resp, bodyBytes, err := sendRequest(http.MethodPost, baseUrl, bytes.NewReader(jsonBody))
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
