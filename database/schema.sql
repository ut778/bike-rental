-- database/schema.sql
CREATE DATABASE IF NOT EXISTS vehicle_rental;
USE vehicle_rental;

-- 1. users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. admins table
CREATE TABLE admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. vehicles table
CREATE TABLE vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) NOT NULL UNIQUE,
    model VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    rent_per_hour DECIMAL(10, 2) NOT NULL,
    availability_status BOOLEAN DEFAULT TRUE
);

-- 4. bookings table
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    total_hours INT NOT NULL,
    total_rent DECIMAL(10, 2) NOT NULL,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE RESTRICT,
    CONSTRAINT chk_end_time CHECK (end_time > start_time)
);

-- Indexing on frequently searched columns
CREATE INDEX idx_vehicle_model ON vehicles(model);
CREATE INDEX idx_vehicle_type ON vehicles(type);
CREATE INDEX idx_booking_user ON bookings(user_id);
CREATE INDEX idx_booking_status ON bookings(status);

-- Triggers

-- Trigger to update vehicle availability when a new booking is created
DELIMITER //
CREATE TRIGGER trg_after_booking_insert
AFTER INSERT ON bookings
FOR EACH ROW
BEGIN
    UPDATE vehicles
    SET availability_status = FALSE
    WHERE vehicle_id = NEW.vehicle_id AND NEW.status = 'active';
END //

-- Trigger to update vehicle availability when a booking is completed or cancelled
CREATE TRIGGER trg_after_booking_update
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF NEW.status IN ('completed', 'cancelled') AND OLD.status = 'active' THEN
        UPDATE vehicles
        SET availability_status = TRUE
        WHERE vehicle_id = NEW.vehicle_id;
    END IF;
END //
DELIMITER ;

-- Stored Procedure

-- Stored procedure to calculate booking cost and create booking
DELIMITER //
CREATE PROCEDURE sp_create_booking(
    IN p_user_id INT,
    IN p_vehicle_id INT,
    IN p_start_time DATETIME,
    IN p_end_time DATETIME
)
BEGIN
    DECLARE v_rent_per_hour DECIMAL(10, 2);
    DECLARE v_total_hours INT;
    DECLARE v_total_rent DECIMAL(10, 2);
    DECLARE v_is_available BOOLEAN;

    -- Start Transaction
    START TRANSACTION;

    -- Check if vehicle is available
    SELECT availability_status INTO v_is_available
    FROM vehicles
    WHERE vehicle_id = p_vehicle_id
    FOR UPDATE; -- Lock the row

    IF v_is_available = TRUE THEN
        -- Get rent per hour
        SELECT rent_per_hour INTO v_rent_per_hour
        FROM vehicles
        WHERE vehicle_id = p_vehicle_id;

        -- Calculate total hours (ceiling to next hour)
        SET v_total_hours = CEIL(TIMESTAMPDIFF(MINUTE, p_start_time, p_end_time) / 60);
        IF v_total_hours <= 0 THEN
            SET v_total_hours = 1; -- Minimum 1 hour
        END IF;

        -- Calculate total rent
        SET v_total_rent = v_total_hours * v_rent_per_hour;

        -- Insert booking
        INSERT INTO bookings (user_id, vehicle_id, start_time, end_time, total_hours, total_rent)
        VALUES (p_user_id, p_vehicle_id, p_start_time, p_end_time, v_total_hours, v_total_rent);

        COMMIT;
        SELECT 'Booking successful' AS message, v_total_rent AS rent;
    ELSE
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vehicle is not available for booking';
    END IF;
END //
DELIMITER ;

-- Sample Data

INSERT INTO admins (username, password_hash) VALUES ('admin', 'scrypt:32768:8:1$u7xK3L$724e38601614742a1f114c679a95724cc63a8a044d0fc3bc8a735c0245a16d5102ab054d5d90938db9b486259ceaf2342006ec143b81180b4317fdbf4e565985'); -- password is 'admin123'
INSERT INTO vehicles (vehicle_number, model, type, rent_per_hour) VALUES
('MH-12-AB-1234', 'Honda City', 'Sedan', 200.00),
('MH-14-CD-5678', 'Hyundai Creta', 'SUV', 300.00),
('MH-12-EF-9012', 'Maruti Swift', 'Hatchback', 150.00),
('MH-12-GH-3456', 'Toyota Innova', 'SUV', 400.00),
('MH-14-IJ-7890', 'Bajaj Dominar', 'Bike', 80.00);
