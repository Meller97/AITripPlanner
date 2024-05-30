import React, { useState } from 'react';

function TripInput() {
  const [formData, setFormData] = useState({
    startDate: '',
    endDate: '',
    budget: '',
    tripType: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form Data:', formData);
    // Here you can handle the submission, e.g., send data to an API
  };

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="startDate">Start Date:</label>
      <input
        type="date"
        id="startDate"
        name="startDate"
        value={formData.startDate}
        onChange={handleChange}
      />

      <label htmlFor="endDate">End Date:</label>
      <input
        type="date"
        id="endDate"
        name="endDate"
        value={formData.endDate}
        onChange={handleChange}
      />

      <label htmlFor="budget">Budget ($):</label>
      <input
        type="number"
        id="budget"
        name="budget"
        value={formData.budget}
        onChange={handleChange}
      />

      <label htmlFor="tripType">Trip Type:</label>
      <select id="tripType" name="tripType" value={formData.tripType} onChange={handleChange}>
        <option value="">Select a type</option>
        <option value="leisure">Leisure</option>
        <option value="business">Business</option>
        <option value="adventure">Adventure</option>
      </select>

      <button type="submit">Submit</button>
    </form>
  );
}

export default TripInput;