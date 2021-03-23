package service

type InternalError struct {
	message string
	err     error
}

func (e *InternalError) Error() string { return e.message + ": " + e.err.Error() }

type RequestError struct {
	message string
	err     error
}

func (e *RequestError) Error() string { return e.message + ": " + e.err.Error() }
