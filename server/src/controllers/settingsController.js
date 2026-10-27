import { dataStore } from '../services/dataStore.js';

export const getSettings = (req, res, next) => {
  try {
    const settings = dataStore.getSettings();
    return res.json({
      success: true,
      data: settings,
    });
  } catch (error) {
    next(error);
  }
};

export const updateSettings = (req, res, next) => {
  try {
    const updated = dataStore.updateSettings(req.body);
    return res.json({
      success: true,
      message: 'Statutory fine schedule and gateway settings updated successfully.',
      data: updated,
    });
  } catch (error) {
    next(error);
  }
};

export const testNotice = (req, res, next) => {
  try {
    const { mobile, plate, violationType, fine } = req.body;
    const challanId = Math.round(1000 + Math.random() * 9000);
    const payUrl = `https://echallan.parivahan.gov.in/portal/pay?challan=E-CH-2026-${challanId}&veh=${plate || 'MH20AB1234'}`;

    const receipt = {
      recipient: mobile || '+919822012345',
      delivery_mode: 'SIMULATED_SMS_LOGGER',
      status: 'SENT',
      timestamp: new Date().toISOString(),
      message_body: `TRAFFIC POLICE NOTICE: E-Challan #${challanId} issued for vehicle ${plate || 'MH20AB1234'}. Violation: ${violationType || 'Red Light Jump'}. Fine Amount: INR ${fine || 1000}. Pay online: ${payUrl}`,
    };

    console.log('\n' + '='.repeat(70));
    console.log(' [STATUTORY SMS DISPATCH RECEIPT]');
    console.log(` To: ${receipt.recipient} | Status: DELIVERED (Simulated)`);
    console.log(` Message: ${receipt.message_body}`);
    console.log('='.repeat(70) + '\n');

    return res.json({
      success: true,
      message: `Test notice dispatched to ${receipt.recipient} [Status: Delivered via Simulation Logger].`,
      data: receipt,
    });
  } catch (error) {
    next(error);
  }
};
