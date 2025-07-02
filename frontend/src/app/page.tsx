"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Edit,
  FileText,
  Loader2,
  Save,
  Trash2,
  Upload,
  XCircle,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { Button } from "@/components/ui/button";
import { useState } from "react";

// Define interfaces for our data structure
interface SalesOrderDetail {
  ProductNumber: string;
  OrderQty: number;
  UnitPrice: number;
  LineTotal: number;
  Name: string;
  Color: string;
  Size: string;
}

interface ExtractedData {
  SalesOrderHeader: { [key: string]: any };
  SalesOrderDetail: SalesOrderDetail[];
  CustomerInfo: string;
  BillingAddress: string;
  ShippingAddress: string;
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(
    null
  );
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
      setExtractedData(null); // Reset on new file selection
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsLoading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      if (response.ok && result.status === "success") {
        setExtractedData(result.data);
      } else {
        console.error("Upload failed:", result.error);
      }
    } catch (error) {
      console.error("Error during upload:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDataChange = (
    section: keyof ExtractedData,
    key: string,
    value: any,
    index?: number
  ) => {
    if (!extractedData) return;

    const newData = { ...extractedData };
    if (section === "SalesOrderDetail" && index !== undefined) {
      newData.SalesOrderDetail[index] = {
        ...newData.SalesOrderDetail[index],
        [key]: value,
      };
    } else if (section === "SalesOrderHeader") {
      newData.SalesOrderHeader[key] = value;
    } else if (
      section === "CustomerInfo" ||
      section === "BillingAddress" ||
      section === "ShippingAddress"
    ) {
      (newData[section] as any) = value;
    }

    setExtractedData(newData);
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setExtractedData(null);
  };

  const handleSave = async () => {
    if (!extractedData?.SalesOrderHeader?.SalesOrderID) return;

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/sales_order/${extractedData.SalesOrderHeader.SalesOrderID}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(extractedData),
        }
      );

      const result = await response.json();
      if (response.ok && result.status === "success") {
        console.log("Data saved successfully");
        setIsEditing(false);
      } else {
        console.error("Failed to save data:", result.error);
      }
    } catch (error) {
      console.error("Error saving data:", error);
    }
  };

  const handleDelete = async () => {
    if (!extractedData?.SalesOrderHeader?.SalesOrderID) return;

    if (
      confirm(
        "Are you sure you want to delete this order? This action cannot be undone."
      )
    ) {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/sales_order/${extractedData.SalesOrderHeader.SalesOrderID}`,
          {
            method: "DELETE",
          }
        );

        const result = await response.json();
        if (response.ok && result.status === "success") {
          console.log("Data deleted successfully");
          handleCancel();
        } else {
          console.error("Failed to delete data:", result.error);
        }
      } catch (error) {
        console.error("Error deleting data:", error);
      }
    }
  };

  const renderValue = (value: any) => {
    if (value instanceof Date) {
      return value.toDateString();
    }
    if (typeof value === "object" && value !== null) {
      return JSON.stringify(value);
    }
    return value ?? "N/A";
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 sm:p-12 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-6xl">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-800 dark:text-white">
          Invoice Data Extraction
        </h1>

        {!extractedData && (
          <Card className="w-full max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle>Upload Invoice</CardTitle>
              <CardDescription>
                Select an invoice image to extract, save, and view its data.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center w-full p-6 border-2 border-dashed rounded-lg">
                <input
                  type="file"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                  accept="image/*"
                />
                <label
                  htmlFor="file-upload"
                  className="flex flex-col items-center cursor-pointer text-gray-500 dark:text-gray-400"
                >
                  <Upload className="w-10 h-10 mb-2" />
                  <span>
                    {selectedFile ? selectedFile.name : "Select an image file"}
                  </span>
                </label>
              </div>
              <div className="flex justify-end mt-4 space-x-2">
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />{" "}
                      Extracting...
                    </>
                  ) : (
                    <>
                      <FileText className="mr-2 h-4 w-4" /> Extract Data
                    </>
                  )}
                </Button>
                {selectedFile && (
                  <Button variant="outline" onClick={handleCancel}>
                    <XCircle className="mr-2 h-4 w-4" /> Cancel
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {extractedData && (
          <div className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Extracted Invoice Data</CardTitle>
                  <CardDescription>
                    Sales Order:{" "}
                    {extractedData.SalesOrderHeader.SalesOrderNumber}
                  </CardDescription>
                </div>
                <div className="flex space-x-2">
                  {!isEditing ? (
                    <Button onClick={() => setIsEditing(true)}>
                      <Edit className="mr-2 h-4 w-4" /> Edit
                    </Button>
                  ) : (
                    <Button onClick={handleSave}>
                      <Save className="mr-2 h-4 w-4" /> Save
                    </Button>
                  )}
                  <Button variant="destructive" onClick={handleDelete}>
                    <Trash2 className="mr-2 h-4 w-4" /> Delete
                  </Button>
                  <Button variant="outline" onClick={handleCancel}>
                    <XCircle className="mr-2 h-4 w-4" /> New Upload
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-1">
                  <h3 className="font-semibold">Customer</h3>
                  <input
                    type="text"
                    readOnly={!isEditing}
                    value={extractedData.CustomerInfo || ""}
                    onChange={(e) =>
                      handleDataChange(
                        "CustomerInfo",
                        "CustomerInfo",
                        e.target.value
                      )
                    }
                    className="w-full p-2 border rounded-md bg-gray-50 read-only:bg-gray-100 dark:bg-gray-800 dark:read-only:bg-gray-700"
                  />
                </div>
                <div className="space-y-1">
                  <h3 className="font-semibold">Shipping Address</h3>
                  <textarea
                    readOnly={!isEditing}
                    value={extractedData.ShippingAddress || ""}
                    onChange={(e) =>
                      handleDataChange(
                        "ShippingAddress",
                        "ShippingAddress",
                        e.target.value
                      )
                    }
                    className="w-full p-2 border rounded-md bg-gray-50 read-only:bg-gray-100 dark:bg-gray-800 dark:read-only:bg-gray-700"
                  />
                </div>
                <div className="space-y-1">
                  <h3 className="font-semibold">Billing Address</h3>
                  <textarea
                    readOnly={!isEditing}
                    value={extractedData.BillingAddress || ""}
                    onChange={(e) =>
                      handleDataChange(
                        "BillingAddress",
                        "BillingAddress",
                        e.target.value
                      )
                    }
                    className="w-full p-2 border rounded-md bg-gray-50 read-only:bg-gray-100 dark:bg-gray-800 dark:read-only:bg-gray-700"
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Order Details</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {Object.entries(extractedData.SalesOrderHeader).map(
                  ([key, value]) => (
                    <div key={key}>
                      <label className="font-semibold text-gray-600 dark:text-gray-400">
                        {key}
                      </label>
                      <input
                        type="text"
                        readOnly={!isEditing}
                        value={renderValue(value)}
                        onChange={(e) =>
                          handleDataChange(
                            "SalesOrderHeader",
                            key,
                            e.target.value
                          )
                        }
                        className="w-full mt-1 p-2 border rounded-md bg-gray-50 read-only:bg-gray-100 dark:bg-gray-800 dark:read-only:bg-gray-700"
                      />
                    </div>
                  )
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Products</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Product</TableHead>
                      <TableHead>Color</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Line Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {extractedData.SalesOrderDetail.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <input
                            type="text"
                            readOnly={!isEditing}
                            value={item.Name || ""}
                            onChange={(e) =>
                              handleDataChange(
                                "SalesOrderDetail",
                                "Name",
                                e.target.value,
                                index
                              )
                            }
                            className="w-full bg-transparent border-none read-only:bg-transparent p-0"
                          />
                        </TableCell>
                        <TableCell>
                          <input
                            type="text"
                            readOnly={!isEditing}
                            value={item.Color || ""}
                            onChange={(e) =>
                              handleDataChange(
                                "SalesOrderDetail",
                                "Color",
                                e.target.value,
                                index
                              )
                            }
                            className="w-full bg-transparent border-none read-only:bg-transparent p-0"
                          />
                        </TableCell>
                        <TableCell>
                          <input
                            type="text"
                            readOnly={!isEditing}
                            value={renderValue(item.Size)}
                            onChange={(e) =>
                              handleDataChange(
                                "SalesOrderDetail",
                                "Size",
                                e.target.value,
                                index
                              )
                            }
                            className="w-full bg-transparent border-none read-only:bg-transparent p-0"
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <input
                            type="number"
                            readOnly={!isEditing}
                            value={item.OrderQty ?? ""}
                            onChange={(e) =>
                              handleDataChange(
                                "SalesOrderDetail",
                                "OrderQty",
                                e.target.value,
                                index
                              )
                            }
                            className="w-full bg-transparent border-none read-only:bg-transparent p-0 text-right"
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <input
                            type="number"
                            readOnly={!isEditing}
                            value={item.UnitPrice ?? ""}
                            onChange={(e) =>
                              handleDataChange(
                                "SalesOrderDetail",
                                "UnitPrice",
                                e.target.value,
                                index
                              )
                            }
                            className="w-full bg-transparent border-none read-only:bg-transparent p-0 text-right"
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <input
                            type="number"
                            readOnly={!isEditing}
                            value={item.LineTotal ?? ""}
                            onChange={(e) =>
                              handleDataChange(
                                "SalesOrderDetail",
                                "LineTotal",
                                e.target.value,
                                index
                              )
                            }
                            className="w-full bg-transparent border-none read-only:bg-transparent p-0 text-right"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </main>
  );
}
